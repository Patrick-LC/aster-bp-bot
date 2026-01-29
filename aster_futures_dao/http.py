import time
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional


class AsterFuturesClient:
    """
    Aster Futures API HTTP客户端
    支持合约交易的HTTP请求和签名
    """
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://fapi.asterdex.com", debug: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.debug = debug
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        # 时间同步相关
        self._time_offset = 0
        self._last_sync_time = 0
        
    def _get_server_time(self) -> int:
        """获取服务器时间"""
        try:
            resp = self.session.get(f"{self.base_url}/fapi/v1/time", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return int(data.get('serverTime', 0))
        except Exception as e:
            if self.debug:
                print(f"[AsterFuturesClient] 获取服务器时间失败: {e}")
            return int(time.time() * 1000)
    
    def _sync_time(self):
        """同步服务器时间"""
        try:
            server_time = self._get_server_time()
            local_time = int(time.time() * 1000)
            self._time_offset = server_time - local_time
            self._last_sync_time = local_time
            if self.debug:
                print(f"[AsterFuturesClient] 时间同步: server={server_time}, local={local_time}, offset={self._time_offset}ms")
        except Exception as e:
            if self.debug:
                print(f"[AsterFuturesClient] 时间同步失败: {e}")
    
    def _get_timestamp(self) -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000) + self._time_offset
    
    def _create_signature(self, query_string: str) -> str:
        """创建HMAC SHA256签名"""
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _prepare_params(self, params: Dict[str, Any], signed: bool = False) -> Dict[str, Any]:
        """准备请求参数"""
        if not signed:
            return params
        
        # 添加时间戳
        params['timestamp'] = self._get_timestamp()
        
        # 创建查询字符串（排除signature字段）
        filtered_params = {k: v for k, v in params.items() if k != 'signature'}
        
        # Aster合约API要求的参数顺序
        param_order = [
            'symbol', 'side', 'type', 'quantity', 'price', 'timeInForce', 
            'positionSide', 'reduceOnly', 'newClientOrderId', 'stopPrice', 
            'closePosition', 'activationPrice', 'callbackRate', 'workingType', 
            'priceProtect', 'newOrderRespType', 'orderId', 'origClientOrderId',
            'recvWindow', 'timestamp'
        ]
        
        # 按指定顺序构建查询字符串
        query_parts = []
        for key in param_order:
            if key in filtered_params:
                query_parts.append(f"{key}={filtered_params[key]}")
        
        # 添加其他参数（按字母顺序）
        remaining_params = {k: v for k, v in filtered_params.items() if k not in param_order}
        for key in sorted(remaining_params.keys()):
            query_parts.append(f"{key}={remaining_params[key]}")
        
        query_string = '&'.join(query_parts)
        
        # 创建签名
        signature = self._create_signature(query_string)
        params['signature'] = signature
        
        if self.debug:
            print(f"[AsterFuturesClient] 签名查询字符串: {query_string}")
            print(f"[AsterFuturesClient] 签名: {signature}")
        
        return params
    
    def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, 
                signed: bool = False, _retry: int = 0) -> Any:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, DELETE等)
            path: API路径
            params: 请求参数
            signed: 是否需要签名
            _retry: 重试次数（内部使用）
        """
        if params is None:
            params = {}
        
        # 同步时间（每5分钟同步一次）
        current_time = int(time.time() * 1000)
        if current_time - self._last_sync_time > 300000:  # 5分钟
            self._sync_time()
        
        # 准备参数
        if signed:
            params = self._prepare_params(params, signed=True)
        
        url = f"{self.base_url}{path}"
        
        if self.debug:
            print(f"[AsterFuturesClient] {method} {url}")
            print(f"[AsterFuturesClient] 参数: {params}")
        
        try:
            if method.upper() == 'GET':
                resp = self.session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                resp = self.session.post(url, data=params, timeout=30)
            elif method.upper() == 'DELETE':
                resp = self.session.delete(url, data=params, timeout=30)
            elif method.upper() == 'PUT':
                resp = self.session.put(url, data=params, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            resp.raise_for_status()
            return resp.json()
            
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 400:
                try:
                    error_data = resp.json()
                    error_code = error_data.get('code', 0)
                    error_msg = error_data.get('msg', '')
                    
                    # 处理时间戳错误
                    if error_code == -1021 and _retry < 2:  # INVALID_TIMESTAMP
                        if self.debug:
                            print(f"[AsterFuturesClient] 检测到时间戳错误，重新同步时间...")
                        self._sync_time()
                        return self.request(method, path, params, signed, _retry + 1)
                    
                    # 处理签名错误
                    elif error_code == -1022 and _retry < 2:  # INVALID_SIGNATURE
                        if self.debug:
                            print(f"[AsterFuturesClient] 检测到签名错误，重新同步时间...")
                        self._sync_time()
                        return self.request(method, path, params, signed, _retry + 1)
                    
                    raise requests.HTTPError(f"HTTP {resp.status_code}: {error_data}")
                except ValueError:
                    raise requests.HTTPError(f"HTTP {resp.status_code}: {resp.text}")
            else:
                raise requests.HTTPError(f"HTTP {resp.status_code}: {resp.text}")
        
        except Exception as e:
            if self.debug:
                print(f"[AsterFuturesClient] 请求异常: {e}")
            raise
