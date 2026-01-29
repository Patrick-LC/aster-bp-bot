import hashlib
import hmac
import time
from typing import Any, Dict, Optional, Tuple, List

import requests


class AsterClient:
	"""Low-level HTTP client handling signing and requests for Aster Spot API."""

	def __init__(
		self,
		api_key: Optional[str] = None,
		api_secret: Optional[str] = None,
		base_url: str = "https://sapi.asterdex.com",
		timeout_seconds: int = 15,
		auto_time_sync: bool = True,
		debug: bool = False,
	):
		self.api_key = api_key
		self.api_secret = api_secret
		self.base_url = base_url.rstrip("/")
		self.session = requests.Session()
		self.timeout_seconds = timeout_seconds
		self.time_offset_ms = 0
		self.auto_time_sync = auto_time_sync
		self.debug = debug
		if self.auto_time_sync:
			try:
				self.sync_time()
			except Exception as e:
				if self.debug:
					print(f"[AsterClient] time sync failed: {e}")
				# ignore sync failure; will retry on demand

	def sync_time(self) -> None:
		"""Sync local offset with server time to avoid INVALID_TIMESTAMP (-1021)."""
		url = f"{self.base_url}/api/v1/time"
		resp = self.session.get(url, timeout=self.timeout_seconds)
		resp.raise_for_status()
		data = resp.json()
		server_time = int(data.get("serverTime"))
		local_time = int(time.time() * 1000)
		self.time_offset_ms = server_time - local_time
		if self.debug:
			print(f"[AsterClient] time sync: server={server_time}, local={local_time}, offset={self.time_offset_ms}ms")

	def _headers(self, needs_key: bool) -> Dict[str, str]:
		headers: Dict[str, str] = {
			"Accept": "application/json",
			"Content-Type": "application/x-www-form-urlencoded",
		}
		if needs_key and self.api_key:
			headers["X-MBX-APIKEY"] = self.api_key
		return headers

	def _hmac_sha256(self, message: str) -> str:
		if not self.api_secret:
			raise ValueError("api_secret is required for signed endpoints")
		secret_bytes = self.api_secret.encode()
		msg_bytes = message.encode()
		signature = hmac.new(secret_bytes, msg_bytes, hashlib.sha256).hexdigest()
		return signature

	@staticmethod
	def _encode_sequence(seq: List[Tuple[str, Any]]) -> str:
		parts: List[str] = []
		for key, value in seq:
			if value is None:
				continue
			parts.append(f"{key}={value}")
		return "&".join(parts)

	def _prepare(self, signed: bool, params: Optional[Dict[str, Any]]) -> Tuple[List[Tuple[str, Any]], bool, Optional[str]]:
		# preserve insertion order of params
		params = dict(params or {})
		needs_key = signed
		debug_signing_string: Optional[str] = None

		seq: List[Tuple[str, Any]] = []
		for k, v in params.items():
			seq.append((k, v))

		if signed:
			# ensure timestamp present using server-adjusted offset
			if "timestamp" not in params:
				current_ms = int(time.time() * 1000 + self.time_offset_ms)
				seq.append(("timestamp", current_ms))
			# default recvWindow under 60s if not provided
			if "recvWindow" not in params:
				seq.append(("recvWindow", 5000))
			# build signing string without signature
			signing_string = self._encode_sequence(seq)
			signature = self._hmac_sha256(signing_string)
			seq.append(("signature", signature))
			debug_signing_string = signing_string
		return seq, needs_key, debug_signing_string

	def request(
		self,
		method: str,
		path: str,
		params: Optional[Dict[str, Any]] = None,
		signed: bool = False,
		use_query: bool = True,
		_retry: bool = False,
	) -> Any:
		"""Generic request wrapper with optional signed HMAC and -1021 retry.
		Ensures the exact same parameter sequence is used for signing and sending."""
		seq, needs_key, debug_sign = self._prepare(signed, params)
		encoded = self._encode_sequence(seq)
		url = f"{self.base_url}{path}"
		headers = self._headers(needs_key)
		method_upper = method.upper()

		if self.debug:
			print(f"[AsterClient] {method_upper} {path}")
			if signed:
				print(f"[AsterClient] signing_string: {debug_sign}")
			print(f"[AsterClient] sending as {'query' if (method_upper in ('GET','DELETE') or use_query) else 'body'}: {encoded}")

		if method_upper in ("GET", "DELETE") or use_query:
			# pass as ordered list of tuples to preserve order
			resp = self.session.request(
				method_upper,
				url,
				params=seq,
				headers=headers,
				timeout=self.timeout_seconds,
			)
		else:
			# Send as body (form-encoded)
			resp = self.session.request(
				method_upper,
				url,
				data=encoded,
				headers=headers,
				timeout=self.timeout_seconds,
			)

		if resp.status_code >= 400:
			# Raise detailed error with payload when possible
			payload: Any
			try:
				payload = resp.json()
			except Exception:
				payload = {"text": resp.text}
			if self.debug:
				print(f"[AsterClient] HTTP {resp.status_code} error payload: {payload}")
			# If timestamp invalid, re-sync and retry once
			if (
				signed
				and not _retry
				and isinstance(payload, dict)
				and payload.get("code") == -1021
			):
				try:
					if self.debug:
						print("[AsterClient] detected -1021, resyncing time and retrying once...")
					self.sync_time()
					return self.request(method, path, params=params, signed=signed, use_query=use_query, _retry=True)
				except Exception as e:
					if self.debug:
						print(f"[AsterClient] retry failed to resync: {e}")
			raise requests.HTTPError(f"HTTP {resp.status_code}: {payload}")

		if resp.headers.get("Content-Type", "").startswith("application/json"):
			return resp.json()
		return resp.text
