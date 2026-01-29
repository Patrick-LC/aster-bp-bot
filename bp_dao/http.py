import base64
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from nacl import signing
from email.utils import parsedate_to_datetime


class BackpackClient:
	"""HTTP client for Backpack Exchange with ED25519 signing."""

	def __init__(
		self,
		api_public_key_b64: Optional[str] = None,
		api_secret_key_b64: Optional[str] = None,
		base_url: str = "https://api.backpack.exchange",
		timeout_seconds: int = 15,
		default_window_ms: int = 30000,
		debug: bool = False,
	):
		self.api_public_key_b64 = api_public_key_b64
		self.api_secret_key_b64 = api_secret_key_b64
		self.base_url = base_url.rstrip("/")
		self.session = requests.Session()
		self.timeout_seconds = timeout_seconds
		self.default_window_ms = default_window_ms
		self.debug = debug
		self._signing_key: Optional[signing.SigningKey] = None
		self._time_offset_ms: int = 0
		if self.api_secret_key_b64:
			self._signing_key = signing.SigningKey(base64.b64decode(self.api_secret_key_b64))

	def _sync_time_from_date_header(self) -> None:
		try:
			resp = self.session.get(f"{self.base_url}/api/v1/markets", timeout=self.timeout_seconds)
			dh = resp.headers.get("Date")
			if dh:
				server_dt = parsedate_to_datetime(dh)
				server_ms = int(server_dt.timestamp() * 1000)
				local_ms = int(time.time() * 1000)
				self._time_offset_ms = server_ms - local_ms
				if self.debug:
					print(f"[BackpackClient] time sync via Date header: server={server_ms}, local={local_ms}, offset={self._time_offset_ms}ms")
		except Exception as e:
			if self.debug:
				print(f"[BackpackClient] time sync failed: {e}")

	@staticmethod
	def _alphabetical_qs(params: Dict[str, Any]) -> str:
		pairs: List[Tuple[str, Any]] = []
		for k in sorted(params.keys()):
			v = params[k]
			if v is None:
				continue
			pairs.append((k, v))
		return "&".join([f"{k}={v}" for k, v in pairs])

	def _sign(self, instruction: str, params: Optional[Dict[str, Any]], timestamp_ms: int, window_ms: int) -> str:
		if not self._signing_key or not self.api_public_key_b64:
			raise ValueError("Signing requires api_public_key_b64 and api_secret_key_b64")
		payload = f"instruction={instruction}"
		if params:
			payload += ("&" + self._alphabetical_qs(params)) if params else ""
		payload += f"&timestamp={timestamp_ms}&window={window_ms}"
		sig = self._signing_key.sign(payload.encode("utf-8")).signature
		sig_b64 = base64.b64encode(sig).decode("ascii")
		if self.debug:
			print(f"[BackpackClient] signing payload: {payload}")
			print(f"[BackpackClient] signature(b64): {sig_b64}")
		return sig_b64

	def _sign_batch_orders(self, instruction: str, orders: List[Dict[str, Any]], timestamp_ms: int, window_ms: int) -> str:
		if not self._signing_key or not self.api_public_key_b64:
			raise ValueError("Signing requires api_public_key_b64 and api_secret_key_b64")
		parts: List[str] = []
		for order in orders:
			qs = self._alphabetical_qs(order)
			parts.append(f"instruction={instruction}&{qs}")
		payload = "&".join(parts) + f"&timestamp={timestamp_ms}&window={window_ms}"
		sig = self._signing_key.sign(payload.encode("utf-8")).signature
		sig_b64 = base64.b64encode(sig).decode("ascii")
		if self.debug:
			print(f"[BackpackClient] signing payload: {payload}")
			print(f"[BackpackClient] signature(b64): {sig_b64}")
		return sig_b64

	def _headers(self, signed: bool, timestamp_ms: Optional[int], window_ms: Optional[int], signature_b64: Optional[str]) -> Dict[str, str]:
		headers = {"Accept": "application/json", "Content-Type": "application/json"}
		if signed:
			if not self.api_public_key_b64:
				raise ValueError("api_public_key_b64 is required for signed endpoints")
			headers.update(
				{
					"X-API-Key": self.api_public_key_b64,
					"X-Signature": signature_b64 or "",
					"X-Timestamp": str(timestamp_ms or 0),
					"X-Window": str(window_ms or self.default_window_ms),
				}
			)
		return headers

	def request(
		self,
		method: str,
		path: str,
		instruction: Optional[str] = None,
		params: Optional[Dict[str, Any]] = None,
		json_body: Optional[Any] = None,
		signed: bool = False,
		_retry: int = 0,
		_window_override: Optional[int] = None,
	) -> Any:
		url = f"{self.base_url}{path}"
		# 使用本地当前时间毫秒作为 X-Timestamp（不使用偏移）
		now_ms = int(time.time() * 1000)
		window_ms = _window_override if _window_override is not None else (self.default_window_ms if signed else None)
		timestamp_ms = now_ms if signed else None
		signature_b64: Optional[str] = None

		# Build signing payload
		if signed and instruction:
			if isinstance(json_body, list) and instruction == "orderExecute":
				# Batch order signing
				signature_b64 = self._sign_batch_orders(instruction, json_body, timestamp_ms or 0, window_ms or self.default_window_ms)
			else:
				# Query or single-body signing
				signing_params = params if params and method.upper() in ("GET", "DELETE") else (json_body if isinstance(json_body, dict) else None)
				signature_b64 = self._sign(instruction, signing_params or {}, timestamp_ms or 0, window_ms or self.default_window_ms)

		headers = self._headers(signed, timestamp_ms, window_ms, signature_b64)
		if self.debug:
			print(f"[BackpackClient] {method.upper()} {url}")
			if params:
				print(f"[BackpackClient] query params: {params}")
			if json_body is not None:
				print(f"[BackpackClient] json body: {json_body}")
			if signed:
				_dbg = dict(headers)
				_dbg["X-Signature"] = "<redacted>"
				print(f"[BackpackClient] headers: {_dbg}")

		resp = self.session.request(
			method=method.upper(),
			url=url,
			params=params if method.upper() in ("GET",) else None,
			json=json_body if method.upper() in ("POST", "PUT", "DELETE") else None,
			headers=headers,
			timeout=self.timeout_seconds,
		)
		if resp.status_code >= 400:
			try:
				payload = resp.json()
			except Exception:
				payload = {"text": resp.text}
			# Retry on expiration: first, try Date header sync; second, expand window to 60000 with fresh local timestamp
			msg = str(payload.get("message", "")) if isinstance(payload, dict) else ""
			if signed and _retry < 2 and ("expired" in msg.lower()):
				if _retry == 0:
					if self.debug:
						print("[BackpackClient] expired -> syncing via Date header and retry...")
					self._sync_time_from_date_header()
					return self.request(method, path, instruction=instruction, params=params, json_body=json_body, signed=signed, _retry=_retry + 1)
				else:
					if self.debug:
						print("[BackpackClient] expired again -> retry with window=60000 and fresh timestamp...")
					return self.request(method, path, instruction=instruction, params=params, json_body=json_body, signed=signed, _retry=_retry + 1, _window_override=60000)
			raise requests.HTTPError(f"HTTP {resp.status_code}: {payload}")
		if resp.headers.get("Content-Type", "").startswith("application/json"):
			return resp.json()
		return resp.text
