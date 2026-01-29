import asyncio
import os

from aster_dao.http import AsterClient
from aster_dao.market import MarketDataDAO
from aster_dao.trade import TradeDAO
from aster_dao.user_stream import UserStreamDAO
from aster_dao.ws import WebSocketClient


def main():
	api_key = os.getenv("ASTER_API_KEY")
	api_secret = os.getenv("ASTER_API_SECRET")
	client = AsterClient(api_key=api_key, api_secret=api_secret)

	market = MarketDataDAO(client)
	trade = TradeDAO(client)
	user_stream = UserStreamDAO(client)

	print("Ping:", market.ping())
	print("Server time:", market.time())
	print("24h ticker BTCUSDT:", market.ticker_24hr("BTCUSDT"))

	if api_key and api_secret:
		account = trade.account()
		print("Account balances count:", len(account.get("balances", [])))
		lk = user_stream.create_listen_key()
		print("listenKey:", lk)

	async def run_ws():
		ws = WebSocketClient()
		# stream one symbol trade events
		async for msg in ws.connect_and_iter("/ws/btcusdt@trade"):
			print("WS message:", msg)
			break

	asyncio.run(run_ws())


if __name__ == "__main__":
	main()
