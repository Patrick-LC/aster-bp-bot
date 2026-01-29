import sys
import time
from decimal import Decimal, ROUND_DOWN, getcontext
from pathlib import Path

# 保证可直接运行找到 bp_dao
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

import yaml

from bp_dao.http import BackpackClient
from bp_dao.markets import MarketsDAO
from bp_dao.order import OrderDAO

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
	# n = floor(value / increment) * increment
	n = (value // increment) * increment
	# 量化到 increment 的小数位
	return n.quantize(increment, rounding=ROUND_DOWN)


def resolve_symbol(markets: MarketsDAO, requested_symbol: str, base_hint: str = "ASTER", want_perp: bool = False) -> str:
	# 若请求的 symbol 无效，则尝试从全部市场中自动匹配
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
	# 优先包含 PERP 的
	if want_perp:
		perp = [s for s in candidates if "PERP" in s.upper()]
		if perp:
			return perp[0]
	# 否则返回第一个匹配
	if candidates:
		return candidates[0]
	# 回退原符号
	return requested_symbol


def main():
	if len(sys.argv) < 2:
		print("用法: python scripts/bp_short_then_long.py config/bp_trading.yaml")
		sys.exit(1)
	cfg = load_config(sys.argv[1])

	api_pub = cfg["api_public_key_b64"]
	api_sec = cfg["api_secret_key_b64"]
	base_url = cfg.get("base_url", "https://api.backpack.exchange")
	symbol = cfg.get("symbol", "ASTER_USDT")
	quantity = str(cfg.get("quantity", "10"))
	window = int(cfg.get("window", 5000))
	pct = Decimal(str(cfg.get("price_offset_percent", 0.2))) / Decimal("100")
	debug = bool(cfg.get("debug", False))

	client = BackpackClient(api_public_key_b64=api_pub, api_secret_key_b64=api_sec, base_url=base_url, debug=debug, default_window_ms=window)
	markets = MarketsDAO(client)
	orders = OrderDAO(client)

	# 获取市场信息以确定价格步进
	try:
		mk = markets.market(symbol)
	except Exception:
		want_perp = any(x in symbol.upper() for x in ["PERP", "-PERP"])
		actual = resolve_symbol(markets, symbol, base_hint="ASTER", want_perp=want_perp)
		if actual != symbol:
			print(f"提示: 交易对 {symbol} 无效，自动使用 {actual}")
			symbol = actual
			mk = markets.market(symbol)

	# 解析价格步进（优先增量）
	price_increment_s = None
	if isinstance(mk, dict):
		price_increment_s = mk.get("priceIncrement") or mk.get("tickSize") or mk.get("priceTickSize")
		if not price_increment_s:
			# 退化使用小数位推导
			pd = mk.get("priceDecimal") or mk.get("pricePrecision")
			if pd is not None:
				price_increment_s = str(Decimal(1) / (Decimal(10) ** int(pd)))
	if not price_increment_s:
		price_increment_s = "0.0001"  # 保守默认
	price_increment = Decimal(str(price_increment_s))
	price_decimals = decimals_from_tick(str(price_increment))
	if debug:
		print(f"[BP] market price_increment={price_increment} (decimals={price_decimals}) raw_market_keys={list(mk.keys()) if isinstance(mk, dict) else 'N/A'}")

	# 获取最新价格
	ticker = markets.ticker(symbol)
	last_price_s = None
	if isinstance(ticker, dict):
		# Backpack Ticker: last price 可能在 "c" 或 "lastPrice" 字段
		last_price_s = ticker.get("c") or ticker.get("lastPrice") or ticker.get("price")
	if last_price_s is None:
		raise RuntimeError("无法获取最新价格")
	last = Decimal(str(last_price_s))

	# 价格 -0.2% 并按步进向下取整
	short_raw = last * (Decimal("1") - pct)
	short_price = floor_to_increment(short_raw, price_increment)
	short_price_str = format(short_price, f".{price_decimals}f")
	print(f"限价做空价: {short_price_str} (步进: {price_increment}, 小数位: {price_decimals})，symbol={symbol}")

	# 提交做空 10 个（Ask）限价单
	short_resp = orders.execute(
		symbol=symbol,
		side="Ask",
		orderType="Limit",
		price=short_price_str,
		quantity=str(quantity),
	)
	print("做空下单回执:", short_resp)

	print("休眠 10 秒...")
	time.sleep(10)

	# 重新获取最新价格
	ticker2 = markets.ticker(symbol)
	last2_s = None
	if isinstance(ticker2, dict):
		last2_s = ticker2.get("c") or ticker2.get("lastPrice") or ticker2.get("price")
	if last2_s is None:
		raise RuntimeError("无法获取最新价格(2)")
	last2 = Decimal(str(last2_s))

	# 价格 +0.2% 并按步进向下取整（挂多）
	long_raw = last2 * (Decimal("1") + pct)
	long_price = floor_to_increment(long_raw, price_increment)
	long_price_str = format(long_price, f".{price_decimals}f")
	print(f"限价做多价: {long_price_str} (步进: {price_increment}, 小数位: {price_decimals})，symbol={symbol}")

	# 提交做多 10 个（Bid）限价单
	long_resp = orders.execute(
		symbol=symbol,
		side="Bid",
		orderType="Limit",
		price=long_price_str,
		quantity=str(quantity),
	)
	print("做多下单回执:", long_resp)


if __name__ == "__main__":
	main()
