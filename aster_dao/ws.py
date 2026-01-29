import asyncio
import json
from typing import Any, AsyncIterable, Iterable, List, Optional

import websockets


class WebSocketClient:
	"""Minimal websocket client for Aster market/user streams.

	Example:
		ws = WebSocketClient()
		async for msg in ws.connect_and_iter("wss://sstream.asterdex.com/ws/btcusdt@trade"):
			print(msg)
	"""

	def __init__(self, base_ws_url: str = "wss://sstream.asterdex.com"):
		self.base_ws_url = base_ws_url.rstrip("/")

	async def connect(self, path: str) -> websockets.WebSocketClientProtocol:
		url = path if path.startswith("ws") else f"{self.base_ws_url}{path}"
		return await websockets.connect(url, ping_interval=150)

	async def connect_and_iter(self, path: str) -> AsyncIterable[Any]:
		async with await self.connect(path) as ws:
			async for raw in ws:
				try:
					yield json.loads(raw)
				except Exception:
					yield raw

	async def subscribe(self, streams: Iterable[str], id_: int = 1, combined: bool = False) -> AsyncIterable[Any]:
		path = "/stream" if combined else "/ws"
		# For combined true, server expects /stream?streams=a/b; we use /ws and send command instead.
		async with await self.connect(path) as ws:
			payload = {"method": "SUBSCRIBE", "params": list(streams), "id": id_}
			await ws.send(json.dumps(payload))
			async for raw in ws:
				try:
					yield json.loads(raw)
				except Exception:
					yield raw

	async def unsubscribe(self, streams: Iterable[str], id_: int = 1) -> Any:
		async with await self.connect("/ws") as ws:
			payload = {"method": "UNSUBSCRIBE", "params": list(streams), "id": id_}
			await ws.send(json.dumps(payload))
			return await ws.recv()
