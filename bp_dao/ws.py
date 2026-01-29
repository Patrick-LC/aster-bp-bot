import asyncio
import json
from typing import Any, AsyncIterable, Iterable, List, Optional

import websockets


class BackpackWS:
	def __init__(self, base_ws_url: str = "wss://ws.backpack.exchange"):
		self.base_ws_url = base_ws_url.rstrip("/")

	async def connect(self) -> websockets.WebSocketClientProtocol:
		return await websockets.connect(self.base_ws_url, ping_interval=60)

	async def stream(self, params: Iterable[str], signature: Optional[List[str]] = None) -> AsyncIterable[Any]:
		async with await self.connect() as ws:
			payload: dict = {"method": "SUBSCRIBE", "params": list(params)}
			if signature:
				payload["signature"] = signature
			await ws.send(json.dumps(payload))
			async for raw in ws:
				try:
					yield json.loads(raw)
				except Exception:
					yield raw

	async def subscribe_once(self, params: Iterable[str], signature: Optional[List[str]] = None) -> Any:
		async with await self.connect() as ws:
			payload: dict = {"method": "SUBSCRIBE", "params": list(params)}
			if signature:
				payload["signature"] = signature
			await ws.send(json.dumps(payload))
			return await ws.recv()

	async def unsubscribe(self, params: Iterable[str]) -> Any:
		async with await self.connect() as ws:
			payload: dict = {"method": "UNSUBSCRIBE", "params": list(params)}
			await ws.send(json.dumps(payload))
			return await ws.recv()
