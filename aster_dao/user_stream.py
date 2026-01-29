from typing import Any, Dict

from .http import AsterClient


class UserStreamDAO:
	def __init__(self, client: AsterClient):
		self.client = client

	def create_listen_key(self) -> Dict[str, str]:
		return self.client.request("POST", "/api/v1/listenKey", signed=False, use_query=True)

	def keepalive_listen_key(self, listenKey: str) -> Any:
		params = {"listenKey": listenKey}
		return self.client.request("PUT", "/api/v1/listenKey", params=params, signed=False)

	def delete_listen_key(self, listenKey: str) -> Any:
		params = {"listenKey": listenKey}
		return self.client.request("DELETE", "/api/v1/listenKey", params=params, signed=False)
