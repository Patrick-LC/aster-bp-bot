from typing import Any, Dict, List, Optional

from .http import AsterClient


class MarketDataDAO:
	def __init__(self, client: AsterClient):
		self.client = client

	def ping(self) -> Any:
		return self.client.request("GET", "/api/v1/ping")

	def time(self) -> Dict[str, int]:
		return self.client.request("GET", "/api/v1/time")

	def exchange_info(self) -> Dict[str, Any]:
		return self.client.request("GET", "/api/v1/exchangeInfo")

	def depth(self, symbol: str, limit: Optional[int] = None) -> Dict[str, Any]:
		params = {"symbol": symbol}
		if limit is not None:
			params["limit"] = limit
		return self.client.request("GET", "/api/v1/depth", params=params)

	def trades(self, symbol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
		params = {"symbol": symbol}
		if limit is not None:
			params["limit"] = limit
		return self.client.request("GET", "/api/v1/trades", params=params)

	def historical_trades(self, symbol: str, limit: Optional[int] = None, fromId: Optional[int] = None) -> List[Dict[str, Any]]:
		params: Dict[str, Any] = {"symbol": symbol}
		if limit is not None:
			params["limit"] = limit
		if fromId is not None:
			params["fromId"] = fromId
		return self.client.request("GET", "/api/v1/historicalTrades", params=params)

	def agg_trades(
		self,
		symbol: str,
		fromId: Optional[int] = None,
		startTime: Optional[int] = None,
		endTime: Optional[int] = None,
		limit: Optional[int] = None,
	) -> List[Dict[str, Any]]:
		params: Dict[str, Any] = {"symbol": symbol}
		if fromId is not None:
			params["fromId"] = fromId
		if startTime is not None:
			params["startTime"] = startTime
		if endTime is not None:
			params["endTime"] = endTime
		if limit is not None:
			params["limit"] = limit
		return self.client.request("GET", "/api/v1/aggTrades", params=params)

	def klines(
		self,
		symbol: str,
		interval: str,
		startTime: Optional[int] = None,
		endTime: Optional[int] = None,
		limit: Optional[int] = None,
	) -> List[List[Any]]:
		params: Dict[str, Any] = {"symbol": symbol, "interval": interval}
		if startTime is not None:
			params["startTime"] = startTime
		if endTime is not None:
			params["endTime"] = endTime
		if limit is not None:
			params["limit"] = limit
		return self.client.request("GET", "/api/v1/klines", params=params)

	def ticker_24hr(self, symbol: Optional[str] = None) -> Any:
		params: Dict[str, Any] = {}
		if symbol:
			params["symbol"] = symbol
		return self.client.request("GET", "/api/v1/ticker/24hr", params=params or None)

	def ticker_price(self, symbol: Optional[str] = None) -> Any:
		params: Dict[str, Any] = {}
		if symbol:
			params["symbol"] = symbol
		return self.client.request("GET", "/api/v1/ticker/price", params=params or None)

	def book_ticker(self, symbol: Optional[str] = None) -> Any:
		params: Dict[str, Any] = {}
		if symbol:
			params["symbol"] = symbol
		return self.client.request("GET", "/api/v1/ticker/bookTicker", params=params or None)

	def commission_rate(self, symbol: str) -> Dict[str, Any]:
		# Doc marks MARKET_DATA, but includes timestamp/recvWindow; require API key and signature
		params = {"symbol": symbol}
		return self.client.request("GET", "/api/v1/commissionRate", params=params, signed=True)

	def estimate_withdraw_fee(self, chainId: str, asset: str) -> Dict[str, Any]:
		params = {"chainId": chainId, "asset": asset}
		return self.client.request("GET", "/api/v1/aster/withdraw/estimateFee", params=params)
