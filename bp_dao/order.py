from typing import Any, Dict, Optional, List

from .http import BackpackClient


class OrderDAO:
	def __init__(self, client: BackpackClient):
		self.client = client

	def execute(
		self,
		symbol: str,
		side: str,
		orderType: str,
		quantity: Optional[str] = None,
		quoteQuantity: Optional[str] = None,
		price: Optional[str] = None,
		timeInForce: Optional[str] = None,
		clientId: Optional[str] = None,
		reduceOnly: Optional[bool] = None,
	) -> Any:
		# POST /api/v1/orders (batch), instruction: orderExecute
		order: Dict[str, Any] = {
			"symbol": symbol,
			"side": side,
			"orderType": orderType,
		}
		if quantity is not None:
			order["quantity"] = quantity
		if quoteQuantity is not None:
			order["quoteQuantity"] = quoteQuantity
		if price is not None:
			order["price"] = price
		if timeInForce is not None:
			order["timeInForce"] = timeInForce
		if clientId is not None:
			order["clientId"] = clientId
		if reduceOnly is not None:
			order["reduceOnly"] = reduceOnly
		body: List[Dict[str, Any]] = [order]
		return self.client.request("POST", "/api/v1/orders", instruction="orderExecute", json_body=body, signed=True)

	def cancel(self, orderId: Optional[str] = None, clientId: Optional[str] = None, symbol: Optional[str] = None) -> Any:
		# DELETE /api/v1/order, instruction: orderCancel, body requires one of orderId/clientId and symbol
		body: Dict[str, Any] = {}
		if orderId is not None:
			body["orderId"] = str(orderId)
		if clientId is not None:
			body["clientId"] = clientId
		if symbol is not None:
			body["symbol"] = symbol
		return self.client.request("DELETE", "/api/v1/order", instruction="orderCancel", json_body=body, signed=True)

	def get(self, orderId: Optional[str] = None, clientId: Optional[str] = None, symbol: Optional[str] = None) -> Any:
		# GET /api/v1/order, instruction: orderQuery
		params: Dict[str, Any] = {}
		if orderId is not None:
			params["orderId"] = orderId
		if clientId is not None:
			params["clientId"] = clientId
		if symbol is not None:
			params["symbol"] = symbol
		return self.client.request("GET", "/api/v1/order", params=params or None, instruction="orderQuery", signed=True)
