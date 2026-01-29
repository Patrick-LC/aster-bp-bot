import websocket
import json
import threading
import time
from typing import Callable, Dict, Any, Optional


class AsterFuturesWS:
    """
    Aster Futures WebSocket客户端
    提供合约WebSocket数据流订阅功能
    """
    
    def __init__(self, base_url: str = "wss://fstream.asterdex.com", debug: bool = False):
        self.base_url = base_url
        self.debug = debug
        self.ws = None
        self.connected = False
        self.subscriptions = set()
        self.message_handlers = {}
        self.heartbeat_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def _log(self, message: str):
        """调试日志"""
        if self.debug:
            print(f"[AsterFuturesWS] {message}")
    
    def _on_message(self, ws, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            self._log(f"收到消息: {data}")
            
            # 处理订阅确认
            if 'result' in data and 'id' in data:
                if data['result'] is None:
                    self._log(f"订阅成功: {data['id']}")
                else:
                    self._log(f"订阅失败: {data}")
                return
            
            # 处理数据流消息
            if 'stream' in data and 'data' in data:
                stream = data['stream']
                payload = data['data']
                self._handle_stream_data(stream, payload)
            else:
                # 直接处理数据
                self._handle_stream_data('direct', data)
                
        except json.JSONDecodeError as e:
            self._log(f"JSON解析错误: {e}")
        except Exception as e:
            self._log(f"消息处理错误: {e}")
    
    def _handle_stream_data(self, stream: str, data: Any):
        """处理数据流数据"""
        if stream in self.message_handlers:
            try:
                self.message_handlers[stream](data)
            except Exception as e:
                self._log(f"消息处理器错误: {e}")
        else:
            self._log(f"未找到处理器: {stream}")
    
    def _on_error(self, ws, error):
        """处理WebSocket错误"""
        self._log(f"WebSocket错误: {error}")
        self.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """处理WebSocket关闭"""
        self._log(f"WebSocket关闭: {close_status_code} - {close_msg}")
        self.connected = False
        
        # 自动重连
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self._log(f"尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            time.sleep(5)
            self.connect()
        else:
            self._log("达到最大重连次数，停止重连")
    
    def _on_open(self, ws):
        """处理WebSocket连接打开"""
        self._log("WebSocket连接已建立")
        self.connected = True
        self.reconnect_attempts = 0
        
        # 重新订阅所有流
        if self.subscriptions:
            self._log(f"重新订阅 {len(self.subscriptions)} 个流")
            self._subscribe_streams(list(self.subscriptions))
    
    def _subscribe_streams(self, streams: list):
        """订阅数据流"""
        if not self.connected or not self.ws:
            self._log("WebSocket未连接，无法订阅")
            return
        
        # 构建订阅消息
        message = {
            "method": "SUBSCRIBE",
            "params": streams,
            "id": int(time.time() * 1000)
        }
        
        self._log(f"发送订阅消息: {message}")
        self.ws.send(json.dumps(message))
    
    def connect(self):
        """连接WebSocket"""
        if self.connected:
            self._log("WebSocket已连接")
            return
        
        try:
            self._log(f"连接到 {self.base_url}")
            self.ws = websocket.WebSocketApp(
                self.base_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # 在新线程中运行WebSocket
            wst = threading.Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()
            
            # 等待连接建立
            timeout = 10
            while not self.connected and timeout > 0:
                time.sleep(0.1)
                timeout -= 0.1
            
            if not self.connected:
                raise Exception("连接超时")
                
        except Exception as e:
            self._log(f"连接失败: {e}")
            raise
    
    def disconnect(self):
        """断开WebSocket连接"""
        if self.ws:
            self._log("断开WebSocket连接")
            self.ws.close()
            self.connected = False
    
    def subscribe(self, stream: str, handler: Callable[[Any], None]):
        """
        订阅数据流
        
        Args:
            stream: 数据流名称，如 "btcusdt@ticker"
            handler: 消息处理函数
        """
        self._log(f"订阅数据流: {stream}")
        
        # 添加处理器
        self.message_handlers[stream] = handler
        self.subscriptions.add(stream)
        
        # 如果已连接，立即订阅
        if self.connected:
            self._subscribe_streams([stream])
        else:
            # 如果未连接，先连接
            self.connect()
            if self.connected:
                self._subscribe_streams([stream])
    
    def unsubscribe(self, stream: str):
        """
        取消订阅数据流
        
        Args:
            stream: 数据流名称
        """
        self._log(f"取消订阅数据流: {stream}")
        
        if stream in self.message_handlers:
            del self.message_handlers[stream]
        self.subscriptions.discard(stream)
        
        if self.connected and self.ws:
            message = {
                "method": "UNSUBSCRIBE",
                "params": [stream],
                "id": int(time.time() * 1000)
            }
            self.ws.send(json.dumps(message))
    
    def subscribe_ticker(self, symbol: str, handler: Callable[[Any], None]):
        """订阅24hr价格变动数据流"""
        stream = f"{symbol.lower()}@ticker"
        self.subscribe(stream, handler)
    
    def subscribe_depth(self, symbol: str, handler: Callable[[Any], None], levels: int = 5):
        """订阅深度数据流"""
        stream = f"{symbol.lower()}@depth{levels}"
        self.subscribe(stream, handler)
    
    def subscribe_trades(self, symbol: str, handler: Callable[[Any], None]):
        """订阅交易数据流"""
        stream = f"{symbol.lower()}@trade"
        self.subscribe(stream, handler)
    
    def subscribe_agg_trades(self, symbol: str, handler: Callable[[Any], None]):
        """订阅归集交易数据流"""
        stream = f"{symbol.lower()}@aggTrade"
        self.subscribe(stream, handler)
    
    def subscribe_kline(self, symbol: str, interval: str, handler: Callable[[Any], None]):
        """订阅K线数据流"""
        stream = f"{symbol.lower()}@kline_{interval}"
        self.subscribe(stream, handler)
    
    def subscribe_mini_ticker(self, symbol: str, handler: Callable[[Any], None]):
        """订阅精简ticker数据流"""
        stream = f"{symbol.lower()}@miniTicker"
        self.subscribe(stream, handler)
    
    def subscribe_book_ticker(self, symbol: str, handler: Callable[[Any], None]):
        """订阅最优挂单数据流"""
        stream = f"{symbol.lower()}@bookTicker"
        self.subscribe(stream, handler)
    
    def subscribe_mark_price(self, symbol: str, handler: Callable[[Any], None]):
        """订阅标记价格数据流"""
        stream = f"{symbol.lower()}@markPrice"
        self.subscribe(stream, handler)
    
    def subscribe_all_mark_price(self, handler: Callable[[Any], None]):
        """订阅全市场标记价格数据流"""
        stream = "!markPrice@arr"
        self.subscribe(stream, handler)
    
    def subscribe_all_mini_ticker(self, handler: Callable[[Any], None]):
        """订阅全市场精简ticker数据流"""
        stream = "!miniTicker@arr"
        self.subscribe(stream, handler)
    
    def subscribe_all_ticker(self, handler: Callable[[Any], None]):
        """订阅全市场ticker数据流"""
        stream = "!ticker@arr"
        self.subscribe(stream, handler)
    
    def subscribe_all_book_ticker(self, handler: Callable[[Any], None]):
        """订阅全市场最优挂单数据流"""
        stream = "!bookTicker"
        self.subscribe(stream, handler)
