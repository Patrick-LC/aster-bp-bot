import os

from bp_dao.http import BackpackClient
from bp_dao.markets import MarketsDAO
from bp_dao.account import AccountDAO
from bp_dao.order import OrderDAO


def main():
	pub = os.getenv("BP_API_PUB")  # base64 verifying key
	sec = os.getenv("BP_API_SEC")  # base64 signing key (seed)
	client = BackpackClient(api_public_key_b64=pub, api_secret_key_b64=sec, debug=True)

	markets = MarketsDAO(client)
	print("markets sample:", markets.markets())

	if pub and sec:
		acct = AccountDAO(client)
		print("account:", acct.account())
		order = OrderDAO(client)
		# 示例：限价单（如需测试，请填写有效symbol/price/quantity）
		# resp = order.execute(symbol="SOL_USDC", side="Bid", orderType="Limit", price="10", quantity="1")
		# print("order:", resp)


if __name__ == "__main__":
	main()
