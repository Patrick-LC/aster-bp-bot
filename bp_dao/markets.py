from typing import Any, Dict, Optional

from .http import BackpackClient


class MarketsDAO:
	def __init__(self, client: BackpackClient):
		self.client = client

	def markets(self, symbol: Optional[str] = None) -> Any:
		params: Dict[str, Any] = {}
		if symbol:
			params["symbol"] = symbol
		return self.client.request("GET", "/api/v1/markets", params=params or None)

	def market(self, symbol: str) -> Any:
		return self.client.request("GET", "/api/v1/market", params={"symbol": symbol})

	def depth(self, symbol: str, limit: Optional[int] = None) -> Any:
		params: Dict[str, Any] = {"symbol": symbol}
		if limit is not None:
			params["limit"] = limit
		return self.client.request("GET", "/api/v1/depth", params=params)

	def ticker(self, symbol: str) -> Any:
		return self.client.request("GET", "/api/v1/ticker", params={"symbol": symbol})

	def trades(self, symbol: str, limit: Optional[int] = None) -> Any:
		params: Dict[str, Any] = {"symbol": symbol}
		if limit is not None:
			params["limit"] = limit
		return self.client.request("GET", "/api/v1/trades", params=params)
