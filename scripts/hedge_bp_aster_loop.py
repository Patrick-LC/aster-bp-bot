import sys
import time
from decimal import Decimal, ROUND_DOWN, getcontext
from pathlib import Path
from datetime import datetime, timedelta, timezone

# 保证可直接运行找到 aster_dao / bp_dao
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

import yaml

from bp_dao.http import BackpackClient
from bp_dao.markets import MarketsDAO
from bp_dao.order import OrderDAO
from aster_futures_dao.http import AsterFuturesClient
from aster_futures_dao.trade import TradeDAO


getcontext().prec = 28


def load_config(path: str) -> dict:
	p = Path(path)
	if not p.exists():
		raise FileNotFoundError(f"配置文件不存在: {p}")
	with p.open("r", encoding="utf-8") as f:
		return yaml.safe_load(f)


def decimals_from_tick(tick_str: str) -> int:
	try:
		return max(0, -Decimal(str(tick_str)).as_tuple().exponent)
	except Exception:
		return 6


def floor_to_increment(value: Decimal, increment: Decimal) -> Decimal:
	if increment <= 0:
		return value
	# 向下取整到价格步进
	n = (value // increment) * increment
	return n.quantize(increment, rounding=ROUND_DOWN)


def resolve_symbol(markets: MarketsDAO, requested_symbol: str, base_hint: str = "ASTER", want_perp: bool = False) -> str:
	all_mkts = markets.markets()
	candidates = []
	if isinstance(all_mkts, list):
		for m in all_mkts:
			try:
				sym = m.get("symbol") or m.get("s")
				if not sym:
					continue
				if base_hint and base_hint.upper() not in sym.upper():
					continue
				candidates.append(sym)
			except Exception:
				continue
	if want_perp:
		perp = [s for s in candidates if "PERP" in s.upper()]
		if perp:
			return perp[0]
	if candidates:
		return candidates[0]
	return requested_symbol


def get_bp_price_increment_and_decimals(markets: MarketsDAO, symbol: str, debug: bool = False) -> tuple[Decimal, int]:
	mk = markets.market(symbol)
	price_increment_s = None
	if isinstance(mk, dict):
		price_increment_s = mk.get("priceIncrement") or mk.get("tickSize") or mk.get("priceTickSize")
		if not price_increment_s:
			pd = mk.get("priceDecimal") or mk.get("pricePrecision")
			if pd is not None:
				price_increment_s = str(Decimal(1) / (Decimal(10) ** int(pd)))
	if not price_increment_s:
		price_increment_s = "0.0001"
	price_increment = Decimal(str(price_increment_s))
	price_decimals = decimals_from_tick(str(price_increment))
	if debug:
		print(f"[BP] market price_increment={price_increment} (decimals={price_decimals}) raw_market_keys={list(mk.keys()) if isinstance(mk, dict) else 'N/A'}")
	return price_increment, price_decimals


def get_bp_last_price(markets: MarketsDAO, symbol: str) -> Decimal:
	ticker = markets.ticker(symbol)
	last_price_s = None
	if isinstance(ticker, dict):
		last_price_s = ticker.get("c") or ticker.get("lastPrice") or ticker.get("price")
	if last_price_s is None:
		raise RuntimeError("无法获取最新价格")
	return Decimal(str(last_price_s))


def place_bp_limit_order(orders: OrderDAO, symbol: str, side: str, price_str: str, quantity: str) -> dict:
	return orders.execute(
		symbol=symbol,
		side=side,
		orderType="Limit",
		price=price_str,
		quantity=str(quantity),
	)


def extract_bp_order_id(resp: dict) -> str:
	# Backpack batch execute returns list; take first entry's orderId
	if isinstance(resp, list) and resp:
		item = resp[0]
		return str(item.get("orderId") or item.get("id") or item.get("orderID") or "")
	if isinstance(resp, dict):
		return str(resp.get("orderId") or resp.get("id") or resp.get("orderID") or "")
	return ""


def check_bp_order_status_alternative(orders: OrderDAO, order_id: str, symbol: str) -> tuple[bool, str]:
	"""
	检查订单状态的替代方法，处理404错误
	返回: (是否成交, 状态信息)
	"""
	try:
		info = orders.get(orderId=order_id, symbol=symbol)
		if isinstance(info, dict):
			status = str(info.get("status") or "").upper()
			if status == "FILLED":
				return True, "FILLED"
			filled = Decimal(str(info.get("filledQuantity") or info.get("executedQty") or "0"))
			qty = Decimal(str(info.get("quantity") or info.get("origQty") or "0"))
			if qty > 0 and filled >= qty:
				return True, f"FILLED (filled: {filled}, total: {qty})"
			return False, f"PENDING (filled: {filled}, total: {qty})"
		return False, "UNKNOWN"
	except Exception as e:
		error_msg = str(e)
		# 如果是404错误，可能是订单已成交或不存在
		if "404" in error_msg or "RESOURCE_NOT_FOUND" in error_msg:
			print(f"[DEBUG] 订单 {order_id} 查询返回404，可能已成交或不存在")
			# 对于404，我们假设订单可能已成交，但需要进一步确认
			return None, "NOT_FOUND_MAYBE_FILLED"
		else:
			print(f"[DEBUG] 查询订单 {order_id} 时发生其他错误: {e}")
			return False, f"ERROR: {error_msg}"


def cancel_bp_order(orders: OrderDAO, order_id: str, symbol: str) -> dict:
	return orders.cancel(orderId=order_id, symbol=symbol)


def hedge_on_aster(trade: TradeDAO, symbol: str, side: str, quantity: str, recv_window: int) -> dict:
	return trade.place_order(
		symbol=symbol,
		side=side,
		order_type="MARKET",
		quantity=float(quantity),
		recv_window=recv_window,
	)


def get_next_funding_time() -> datetime:
	"""
	获取下一个资金费率结算时间（每8小时一次：00:00, 08:00, 16:00 UTC）
	"""
	now = datetime.now(timezone.utc)
	hour = now.hour
	
	# 计算下一个资金费率时间
	if hour < 8:
		next_hour = 8
	elif hour < 16:
		next_hour = 16
	else:
		next_hour = 24  # 明天00:00
	
	next_funding = now.replace(hour=next_hour % 24, minute=0, second=0, microsecond=0)
	if next_hour == 24:
		next_funding += timedelta(days=1)
	
	return next_funding


def should_stop_for_funding(stop_before_minutes: int = 5) -> tuple[bool, str]:
	"""
	检查是否应该停止交易以等待资金费率
	返回: (是否应该停止, 原因说明)
	"""
	now = datetime.now(timezone.utc)
	next_funding = get_next_funding_time()
	time_to_funding = next_funding - now
	
	# 如果距离资金费率时间少于指定分钟数，则停止
	if time_to_funding.total_seconds() <= stop_before_minutes * 60:
		minutes_left = int(time_to_funding.total_seconds() / 60)
		seconds_left = int(time_to_funding.total_seconds() % 60)
		return True, f"距离资金费率时间 {next_funding.strftime('%H:%M')} UTC 还有 {minutes_left}分{seconds_left}秒"
	
	return False, f"距离资金费率时间 {next_funding.strftime('%H:%M')} UTC 还有 {int(time_to_funding.total_seconds()/60)}分钟"


def wait_until_funding_time():
	"""
	等待到资金费率时间，然后继续
	"""
	next_funding = get_next_funding_time()
	now = datetime.now(timezone.utc)
	wait_seconds = (next_funding - now).total_seconds()
	
	if wait_seconds > 0:
		print(f"等待资金费率时间 {next_funding.strftime('%H:%M')} UTC...")
		print(f"预计等待 {int(wait_seconds/60)} 分钟")
		
		# 每分钟输出一次等待状态
		while wait_seconds > 0:
			minutes_left = int(wait_seconds / 60)
			seconds_left = int(wait_seconds % 60)
			print(f"等待中... 还有 {minutes_left}分{seconds_left}秒")
			
			# 等待1分钟或剩余时间（取较小值）
			sleep_time = min(60, wait_seconds)
			time.sleep(sleep_time)
			wait_seconds -= sleep_time
		
		print("资金费率时间已到，继续执行对冲策略...")


def execute_hedge_cycle(bp_markets, bp_orders, aster_trade, bp_symbol, aster_symbol, 
						quantity, offset_percent, price_increment, price_decimals, 
						first_wait_seconds, recv_window, cycle_count):
	"""
	执行一轮完整的对冲策略
	"""
	print(f"[Cycle {cycle_count}] 开始执行对冲策略")
	
	# ---------- 第一腿：BP 做空，ASTER 市价买入对冲 ----------
	try:
		last = get_bp_last_price(bp_markets, bp_symbol)
		# 价格 +0.2% 做空（Ask）
		short_raw = last * (Decimal("1") + offset_percent)
		short_price = floor_to_increment(short_raw, price_increment)
		short_price_str = format(short_price, f".{price_decimals}f")
		print(f"[Leg1] BP 限价做空价: {short_price_str} (基于最新价 {last})，symbol={bp_symbol}")

		resp = place_bp_limit_order(bp_orders, bp_symbol, side="Ask", price_str=short_price_str, quantity=quantity)
		print("[Leg1] BP 做空下单回执:", resp)
		order_id = extract_bp_order_id(resp)
		if not order_id:
			raise RuntimeError("无法解析 BP 订单ID")

		# 持续监控直到成交为止
		filled = False
		monitor_start = time.time()
		retry_count = 0
		max_retries = 20  # 最多重试20次
		
		print(f"[Leg1] 开始监控 BP 做空订单 {order_id}，将持续监控直到成交...")
		
		while not filled and retry_count <= max_retries:
			elapsed = int(time.time() - monitor_start)
			
			# 使用新的状态检查函数
			status_result, status_info = check_bp_order_status_alternative(bp_orders, order_id, bp_symbol)
			
			if status_result is True:
				filled = True
				print(f"[Leg1] BP 做空订单 {order_id} 已成交！总耗时 {elapsed} 秒，状态: {status_info}")
				break
			elif status_result is None:  # 404错误，可能已成交
				print(f"[Leg1] 订单 {order_id} 查询返回404，可能已成交，尝试执行对冲...")
				filled = True  # 假设已成交，执行对冲
				break
			
			# 每1秒输出一次监控日志
			if elapsed % 1 == 0 and elapsed > 0:
				print(f"[Leg1] 监控中... 已等待 {elapsed}s，订单 {order_id} 未成交")
			
			# 每10秒检查一次是否需要重新挂单
			if elapsed > 0 and elapsed % 10 == 0 and retry_count < max_retries:
				print(f"[Leg1] 已等待 {elapsed} 秒，取消当前订单并重新挂单...")
				try:
					_ = cancel_bp_order(bp_orders, order_id, bp_symbol)
					print(f"[Leg1] 订单 {order_id} 已取消")
				except Exception as e:
					print(f"[Leg1] 取消失败: {e}")
					# 如果取消失败（可能是订单已成交），检查状态
					status_result, status_info = check_bp_order_status_alternative(bp_orders, order_id, bp_symbol)
					if status_result is None:  # 404错误，可能已成交
						print(f"[Leg1] 取消失败但订单可能已成交，尝试执行对冲...")
						filled = True
						break
				
				# 使用最新价重算 +0.2%
				last = get_bp_last_price(bp_markets, bp_symbol)
				short_raw = last * (Decimal("1") + offset_percent)
				short_price = floor_to_increment(short_raw, price_increment)
				short_price_str = format(short_price, f".{price_decimals}f")
				print(f"[Leg1] 重新挂单，最新价: {last}，挂单价: {short_price_str}")
				
				resp = place_bp_limit_order(bp_orders, bp_symbol, side="Ask", price_str=short_price_str, quantity=quantity)
				print("[Leg1] BP 重挂做空回执:", resp)
				order_id = extract_bp_order_id(resp)
				if not order_id:
					raise RuntimeError("无法解析重挂后的 BP 订单ID")
				
				retry_count += 1
				print(f"[Leg1] 第 {retry_count} 次重挂完成，继续监控订单 {order_id}...")
			
			time.sleep(1)

		if filled:
			print("[Leg1] BP 做空已成交，ASTER 市价买入对冲...")
			buy_resp = hedge_on_aster(aster_trade, aster_symbol, side="BUY", quantity=quantity, recv_window=recv_window)
			print("[Leg1] ASTER 市价买入回执:", buy_resp)
		else:
			print(f"[Leg1] 警告：BP 做空在 {max_retries} 次重试后仍未成交，跳过对冲。")
	except Exception as e:
		print(f"[Leg1] 异常: {e}")

		print(f"休眠 20 秒...")
		time.sleep(20)


	# ---------- 第二腿：BP 做多，ASTER 市价卖出对冲 ----------
	try:
		last = get_bp_last_price(bp_markets, bp_symbol)
		# 价格 -0.2% 做多（Bid）
		long_raw = last * (Decimal("1") - offset_percent)
		long_price = floor_to_increment(long_raw, price_increment)
		long_price_str = format(long_price, f".{price_decimals}f")
		print(f"[Leg2] BP 限价做多价: {long_price_str} (基于最新价 {last})，symbol={bp_symbol}")

		resp = place_bp_limit_order(bp_orders, bp_symbol, side="Bid", price_str=long_price_str, quantity=quantity)
		print("[Leg2] BP 做多下单回执:", resp)
		order_id = extract_bp_order_id(resp)
		if not order_id:
			raise RuntimeError("无法解析 BP 订单ID")

		# 持续监控直到成交为止
		filled = False
		monitor_start = time.time()
		retry_count = 0
		max_retries = 20  # 最多重试20次
		
		print(f"[Leg2] 开始监控 BP 做多订单 {order_id}，将持续监控直到成交...")
		
		while not filled and retry_count <= max_retries:
			elapsed = int(time.time() - monitor_start)
			
			# 使用新的状态检查函数
			status_result, status_info = check_bp_order_status_alternative(bp_orders, order_id, bp_symbol)
			
			if status_result is True:
				filled = True
				print(f"[Leg2] BP 做多订单 {order_id} 已成交！总耗时 {elapsed} 秒，状态: {status_info}")
				break
			elif status_result is None:  # 404错误，可能已成交
				print(f"[Leg2] 订单 {order_id} 查询返回404，可能已成交，尝试执行对冲...")
				filled = True  # 假设已成交，执行对冲
				break
			
			# 每1秒输出一次监控日志
			if elapsed % 1 == 0 and elapsed > 0:
				print(f"[Leg2] 监控中... 已等待 {elapsed}s，订单 {order_id} 未成交")
			
			# 每10秒检查一次是否需要重新挂单
			if elapsed > 0 and elapsed % 10 == 0 and retry_count < max_retries:
				print(f"[Leg2] 已等待 {elapsed} 秒，取消当前订单并重新挂单...")
				try:
					_ = cancel_bp_order(bp_orders, order_id, bp_symbol)
					print(f"[Leg2] 订单 {order_id} 已取消")
				except Exception as e:
					print(f"[Leg2] 取消失败: {e}")
					# 如果取消失败（可能是订单已成交），检查状态
					status_result, status_info = check_bp_order_status_alternative(bp_orders, order_id, bp_symbol)
					if status_result is None:  # 404错误，可能已成交
						print(f"[Leg2] 取消失败但订单可能已成交，尝试执行对冲...")
						filled = True
						break
				
				# 使用最新价重算 -0.2%
				last = get_bp_last_price(bp_markets, bp_symbol)
				long_raw = last * (Decimal("1") - offset_percent)
				long_price = floor_to_increment(long_raw, price_increment)
				long_price_str = format(long_price, f".{price_decimals}f")
				print(f"[Leg2] 重新挂单，最新价: {last}，挂单价: {long_price_str}")
				
				resp = place_bp_limit_order(bp_orders, bp_symbol, side="Bid", price_str=long_price_str, quantity=quantity)
				print("[Leg2] BP 重挂做多回执:", resp)
				order_id = extract_bp_order_id(resp)
				if not order_id:
					raise RuntimeError("无法解析重挂后的 BP 订单ID")
				
				retry_count += 1
				print(f"[Leg2] 第 {retry_count} 次重挂完成，继续监控订单 {order_id}...")
			
			time.sleep(1)

		if filled:
			print("[Leg2] BP 做多已成交，ASTER 市价卖出对冲...")
			sell_resp = hedge_on_aster(aster_trade, aster_symbol, side="SELL", quantity=quantity, recv_window=recv_window)
			print("[Leg2] ASTER 市价卖出回执:", sell_resp)
		else:
			print(f"[Leg2] 警告：BP 做多在 {max_retries} 次重试后仍未成交，跳过对冲。")
	except Exception as e:
		print(f"[Leg2] 异常: {e}")


def main():
	if len(sys.argv) < 2:
		print("用法: python scripts/hedge_bp_aster_loop.py config/hedge.yaml")
		sys.exit(1)
	cfg = load_config(sys.argv[1])

	bp_cfg = cfg["bp"]
	aster_cfg = cfg["aster"]
	trade_cfg = cfg.get("trade", {})

	# BP
	bp_client = BackpackClient(
		api_public_key_b64=bp_cfg["api_public_key_b64"],
		api_secret_key_b64=bp_cfg["api_secret_key_b64"],
		base_url=bp_cfg.get("base_url", "https://api.backpack.exchange"),
		debug=bool(bp_cfg.get("debug", False)),
		default_window_ms=int(bp_cfg.get("window", 5000)),
	)
	bp_markets = MarketsDAO(bp_client)
	bp_orders = OrderDAO(bp_client)
	bp_symbol = bp_cfg.get("symbol", "ASTER_USDC_PERP")

	# Aster Futures
	aster_client = AsterFuturesClient(
		api_key=aster_cfg["api_key"],
		api_secret=aster_cfg["api_secret"],
		base_url=aster_cfg.get("base_url", "https://fapi.asterdex.com"),
		debug=bool(aster_cfg.get("debug", False)),
	)
	aster_trade = TradeDAO(aster_client)
	aster_symbol = aster_cfg.get("symbol", "ASTERUSDT")
	recv_window = int(aster_cfg.get("recv_window", 5000))

	quantity = str(trade_cfg.get("quantity", "10"))
	offset_percent = Decimal(str(trade_cfg.get("offset_percent", 0.2))) / Decimal("100")
	first_wait_seconds = int(trade_cfg.get("first_wait_seconds", 10))
	between_sleep = int(trade_cfg.get("between_legs_sleep", 20))
	
	# 资金费率相关配置
	stop_before_funding_minutes = int(trade_cfg.get("stop_before_funding_minutes", 5))  # 资金费率前几分钟停止
	cycle_sleep = int(trade_cfg.get("cycle_sleep", 60))  # 每轮循环间隔秒数

	# 确定符号与步进
	try:
		_ = bp_markets.market(bp_symbol)
	except Exception:
		want_perp = any(x in bp_symbol.upper() for x in ["PERP", "-PERP"])
		actual = resolve_symbol(bp_markets, bp_symbol, base_hint="ASTER", want_perp=want_perp)
		if actual != bp_symbol:
			print(f"提示: 交易对 {bp_symbol} 无效，自动使用 {actual}")
			bp_symbol = actual

	price_increment, price_decimals = get_bp_price_increment_and_decimals(bp_markets, bp_symbol, debug=bp_client.debug)

	print("=" * 60)
	print("开始循环对冲策略")
	print("=" * 60)
	
	cycle_count = 0
	
	while True:
		cycle_count += 1
		print(f"\n[Cycle {cycle_count}] 开始新一轮对冲策略")
		
		# 显示当前资金费率时间信息
		_, reason = should_stop_for_funding(stop_before_funding_minutes)
		print(f"[Cycle {cycle_count}] {reason}")

		# 执行对冲策略
		execute_hedge_cycle(
			bp_markets, bp_orders, aster_trade, bp_symbol, aster_symbol,
			quantity, offset_percent, price_increment, price_decimals,
			first_wait_seconds, recv_window, cycle_count
		)
		
		# 循环间隔
		print(f"[Cycle {cycle_count}] 完成，等待 {cycle_sleep} 秒后开始下一轮...")
		time.sleep(cycle_sleep)


if __name__ == "__main__":
	main()
