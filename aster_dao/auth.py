from typing import Any, Dict, Optional

from .http import AsterClient


class AuthDAO:
	def __init__(self, client: AsterClient):
		self.client = client

	def get_nonce(self, address: str, userOperationType: str = "CREATE_API_KEY", network: Optional[str] = None) -> Any:
		params: Dict[str, Any] = {"address": address, "userOperationType": userOperationType}
		if network is not None:
			params["network"] = network
		return self.client.request("POST", "/api/v1/getNonce", params=params)

	def create_api_key(
		self,
		address: str,
		userSignature: str,
		desc: str,
		network: Optional[str] = None,
		apikeyIP: Optional[str] = None,
		recvWindow: Optional[int] = None,
	) -> Dict[str, Any]:
		params: Dict[str, Any] = {
			"address": address,
			"userOperationType": "CREATE_API_KEY",
			"userSignature": userSignature,
			"desc": desc,
		}
		if network is not None:
			params["network"] = network
		if apikeyIP is not None:
			params["apikeyIP"] = apikeyIP
		if recvWindow is not None:
			params["recvWindow"] = recvWindow
		# createApiKey requires timestamp; mark signed to auto-add timestamp/signature header usage of API key is not required
		return self.client.request("POST", "/api/v1/createApiKey", params=params, signed=True)
