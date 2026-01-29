from typing import Any, Dict, Optional

from .http import BackpackClient


class AccountDAO:
	def __init__(self, client: BackpackClient):
		self.client = client

	def account(self) -> Any:
		# GET /api/v1/account, instruction: accountQuery
		return self.client.request("GET", "/api/v1/account", instruction="accountQuery", signed=True)

	def balances(self) -> Any:
		# GET /api/v1/balances, instruction: balanceQuery
		return self.client.request("GET", "/api/v1/balances", instruction="balanceQuery", signed=True)

	def positions(self, symbol: Optional[str] = None) -> Any:
		# GET /api/v1/positions, instruction: positionQuery
		params: Dict[str, Any] = {}
		if symbol:
			params["symbol"] = symbol
		return self.client.request("GET", "/api/v1/positions", params=params or None, instruction="positionQuery", signed=True)
