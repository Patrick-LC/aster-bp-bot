from typing import Any, Dict, List, Optional

from .http import AsterClient


class TradeDAO:
	def __init__(self, client: AsterClient):
		self.client = client

	def place_order(
		self,
		symbol: str,
		side: str,
		type: str,
		timeInForce: Optional[str] = None,
		quantity: Optional[str] = None,
		quoteOrderQty: Optional[str] = None,
		price: Optional[str] = None,
		newClientOrderId: Optional[str] = None,
		stopPrice: Optional[str] = None,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {
			"symbol": symbol,
			"side": side,
			"type": type,
		}
		if timeInForce is not None:
			params["timeInForce"] = timeInForce
		if quantity is not None:
			params["quantity"] = quantity
		if quoteOrderQty is not None:
			params["quoteOrderQty"] = quoteOrderQty
		if price is not None:
			params["price"] = price
		if newClientOrderId is not None:
			params["newClientOrderId"] = newClientOrderId
		if stopPrice is not None:
			params["stopPrice"] = stopPrice
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("POST", "/api/v1/order", params=params, signed=True)

	def cancel_order(
		self,
		symbol: str,
		orderId: Optional[int] = None,
		origClientOrderId: Optional[str] = None,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {"symbol": symbol}
		if orderId is not None:
			params["orderId"] = orderId
		if origClientOrderId is not None:
			params["origClientOrderId"] = origClientOrderId
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("DELETE", "/api/v1/order", params=params, signed=True)

	def get_order(
		self,
		symbol: str,
		orderId: Optional[int] = None,
		origClientOrderId: Optional[str] = None,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {"symbol": symbol}
		if orderId is not None:
			params["orderId"] = orderId
		if origClientOrderId is not None:
			params["origClientOrderId"] = origClientOrderId
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("GET", "/api/v1/order", params=params, signed=True)

	def get_open_order(
		self,
		symbol: str,
		orderId: Optional[int] = None,
		origClientOrderId: Optional[str] = None,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {"symbol": symbol}
		if orderId is not None:
			params["orderId"] = orderId
		if origClientOrderId is not None:
			params["origClientOrderId"] = origClientOrderId
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("GET", "/api/v1/openOrder", params=params, signed=True)

	def get_open_orders(self, symbol: Optional[str] = None, recvWindow: Optional[int] = None) -> List[Dict[str, Any]]:
		params: Dict[str, Any] = {}
		if symbol is not None:
			params["symbol"] = symbol
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("GET", "/api/v1/openOrders", params=params, signed=True)

	def cancel_all_open_orders(
		self,
		symbol: str,
		orderIdList: Optional[str] = None,
		origClientOrderIdList: Optional[str] = None,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {"symbol": symbol}
		if orderIdList is not None:
			params["orderIdList"] = orderIdList
		if origClientOrderIdList is not None:
			params["origClientOrderIdList"] = origClientOrderIdList
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		# Doc shows "DEL" but actual method should be DELETE
		return self.client.request("DELETE", "/api/v1/allOpenOrders", params=params, signed=True)

	def get_all_orders(
		self,
		symbol: str,
		orderId: Optional[int] = None,
		startTime: Optional[int] = None,
		endTime: Optional[int] = None,
		limit: Optional[int] = None,
		recvWindow: Optional[int] = None,
	) -> List[Dict[str, Any]]:
		params: Dict[str, Any] = {"symbol": symbol}
		if orderId is not None:
			params["orderId"] = orderId
		if startTime is not None:
			params["startTime"] = startTime
		if endTime is not None:
			params["endTime"] = endTime
		if limit is not None:
			params["limit"] = limit
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("GET", "/api/v1/allOrders", params=params, signed=True)

	def account(self, recvWindow: Optional[int] = None) -> Dict[str, Any]:
		params: Dict[str, Any] = {}
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("GET", "/api/v1/account", params=params, signed=True)

	def user_trades(
		self,
		symbol: Optional[str] = None,
		orderId: Optional[int] = None,
		startTime: Optional[int] = None,
		endTime: Optional[int] = None,
		fromId: Optional[int] = None,
		limit: Optional[int] = None,
		recvWindow: Optional[int] = None,
	) -> List[Dict[str, Any]]:
		params: Dict[str, Any] = {}
		if symbol is not None:
			params["symbol"] = symbol
		if orderId is not None:
			params["orderId"] = orderId
		if startTime is not None:
			params["startTime"] = startTime
		if endTime is not None:
			params["endTime"] = endTime
		if fromId is not None:
			params["fromId"] = fromId
		if limit is not None:
			params["limit"] = limit
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("GET", "/api/v1/userTrades", params=params, signed=True)

	def wallet_transfer(
		self,
		amount: str,
		asset: str,
		clientTranId: str,
		kindType: str,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {
			"amount": amount,
			"asset": asset,
			"clientTranId": clientTranId,
			"kindType": kindType,
		}
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("POST", "/api/v1/asset/wallet/transfer", params=params, signed=True)

	def send_to_address(
		self,
		amount: str,
		asset: str,
		toAddress: str,
		clientTranId: Optional[str] = None,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {
			"amount": amount,
			"asset": asset,
			"toAddress": toAddress,
		}
		if clientTranId is not None:
			params["clientTranId"] = clientTranId
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("POST", "/api/v1/asset/sendToAddress", params=params, signed=True)

	def user_withdraw(
		self,
		chainId: str,
		asset: str,
		amount: str,
		fee: str,
		receiver: str,
		nonce: str,
		userSignature: str,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {
			"chainId": chainId,
			"asset": asset,
			"amount": amount,
			"fee": fee,
			"receiver": receiver,
			"nonce": nonce,
			"userSignature": userSignature,
		}
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		return self.client.request("POST", "/api/v1/aster/user-withdraw", params=params, signed=True)
