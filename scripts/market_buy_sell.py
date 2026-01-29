import sys
import time
from pathlib import Path

# 确保可以直接运行脚本时找到项目内的 aster_dao 包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

import yaml

from aster_dao.http import AsterClient
from aster_dao.trade import TradeDAO


def load_config(path: str) -> dict:
	p = Path(path)
	if not p.exists():
		raise FileNotFoundError(f"配置文件不存在: {p}")
	with p.open("r", encoding="utf-8") as f:
		return yaml.safe_load(f)


def main():
	if len(sys.argv) < 2:
		print("用法: python scripts/market_buy_sell.py config/trading.yaml")
		sys.exit(1)
	cfg = load_config(sys.argv[1])

	api_key = cfg["api_key"]
	api_secret = cfg["api_secret"]
	base_url = cfg.get("base_url", "https://sapi.asterdex.com")
	symbol = cfg.get("symbol", "ASTERUSDT")
	quantity = cfg.get("quantity", "10")
	recv_window = int(cfg.get("recv_window", 5000))
	debug = bool(cfg.get("debug", False))

	client = AsterClient(api_key=api_key, api_secret=api_secret, base_url=base_url, debug=debug)
	trade = TradeDAO(client)

	print(f"市价买入 {symbol} 数量 {quantity}...")
	buy_resp = trade.place_order(
		symbol=symbol,
		side="BUY",
		type="MARKET",
		quantity=quantity,
		recvWindow=recv_window,
	)
	print("买入回执:", buy_resp)

	print("等待 10 秒...")
	time.sleep(10)

	print(f"市价卖出 {symbol} 数量 {quantity}...")
	sell_resp = trade.place_order(
		symbol=symbol,
		side="SELL",
		type="MARKET",
		quantity=quantity,
		recvWindow=recv_window,
	)
	print("卖出回执:", sell_resp)


if __name__ == "__main__":
	main()
