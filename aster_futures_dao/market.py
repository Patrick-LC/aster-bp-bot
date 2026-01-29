from typing import Dict, Any, Optional, List


class MarketDataDAO:
    """
    Aster Futures 市场数据DAO
    提供合约市场数据相关接口
    """
    
    def __init__(self, client):
        self.client = client
    
    def ping(self) -> Dict[str, Any]:
        """测试服务器连通性"""
        return self.client.request("GET", "/fapi/v1/ping")
    
    def time(self) -> Dict[str, Any]:
        """获取服务器时间"""
        return self.client.request("GET", "/fapi/v1/time")
    
    def exchange_info(self) -> Dict[str, Any]:
        """获取交易规则和交易对信息"""
        return self.client.request("GET", "/fapi/v1/exchangeInfo")
    
    def depth(self, symbol: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        获取深度信息
        
        Args:
            symbol: 交易对
            limit: 限制档位数量，可选值: 5, 10, 20, 50, 100, 500, 1000
        """
        params = {"symbol": symbol}
        if limit is not None:
            params["limit"] = limit
        return self.client.request("GET", "/fapi/v1/depth", params=params)
    
    def trades(self, symbol: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取近期成交
        
        Args:
            symbol: 交易对
            limit: 限制数量，默认500，最大1000
        """
        params = {"symbol": symbol}
        if limit is not None:
            params["limit"] = limit
        return self.client.request("GET", "/fapi/v1/trades", params=params)
    
    def historical_trades(self, symbol: str, limit: Optional[int] = None, from_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询历史成交
        
        Args:
            symbol: 交易对
            limit: 限制数量，默认500，最大1000
            from_id: 从哪一条成交id开始返回
        """
        params = {"symbol": symbol}
        if limit is not None:
            params["limit"] = limit
        if from_id is not None:
            params["fromId"] = from_id
        return self.client.request("GET", "/fapi/v1/historicalTrades", params=params)
    
    def agg_trades(self, symbol: str, from_id: Optional[int] = None, start_time: Optional[int] = None, 
                   end_time: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取归集交易
        
        Args:
            symbol: 交易对
            from_id: 从包含fromId的成交id开始返回结果
            start_time: 从该时刻之后的成交记录开始返回结果
            end_time: 返回该时刻为止的成交记录
            limit: 限制数量，默认500，最大1000
        """
        params = {"symbol": symbol}
        if from_id is not None:
            params["fromId"] = from_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        return self.client.request("GET", "/fapi/v1/aggTrades", params=params)
    
    def klines(self, symbol: str, interval: str, start_time: Optional[int] = None, 
               end_time: Optional[int] = None, limit: Optional[int] = None) -> List[List]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: K线间隔 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认500，最大1500
        """
        params = {"symbol": symbol, "interval": interval}
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        return self.client.request("GET", "/fapi/v1/klines", params=params)
    
    def index_price_klines(self, pair: str, interval: str, start_time: Optional[int] = None, 
                          end_time: Optional[int] = None, limit: Optional[int] = None) -> List[List]:
        """
        获取价格指数K线数据
        
        Args:
            pair: 标的交易对
            interval: K线间隔
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认500，最大1500
        """
        params = {"pair": pair, "interval": interval}
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        return self.client.request("GET", "/fapi/v1/indexPriceKlines", params=params)
    
    def mark_price_klines(self, symbol: str, interval: str, start_time: Optional[int] = None, 
                         end_time: Optional[int] = None, limit: Optional[int] = None) -> List[List]:
        """
        获取标记价格K线数据
        
        Args:
            symbol: 交易对
            interval: K线间隔
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认500，最大1500
        """
        params = {"symbol": symbol, "interval": interval}
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        return self.client.request("GET", "/fapi/v1/markPriceKlines", params=params)
    
    def premium_index(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取最新标记价格和资金费率
        
        Args:
            symbol: 交易对，不传则返回所有交易对
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        return self.client.request("GET", "/fapi/v1/premiumIndex", params=params)
    
    def funding_rate(self, symbol: Optional[str] = None, start_time: Optional[int] = None, 
                     end_time: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询资金费率历史
        
        Args:
            symbol: 交易对
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认100，最大1000
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        return self.client.request("GET", "/fapi/v1/fundingRate", params=params)
    
    def funding_info(self) -> List[Dict[str, Any]]:
        """查询资金费率配置"""
        return self.client.request("GET", "/fapi/v1/fundingInfo")
    
    def ticker_24hr(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取24hr价格变动情况
        
        Args:
            symbol: 交易对，不传则返回所有交易对
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        return self.client.request("GET", "/fapi/v1/ticker/24hr", params=params)
    
    def ticker_price(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取最新价格
        
        Args:
            symbol: 交易对，不传则返回所有交易对
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        return self.client.request("GET", "/fapi/v1/ticker/price", params=params)
    
    def ticker_book(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        获取当前最优挂单
        
        Args:
            symbol: 交易对，不传则返回所有交易对
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        return self.client.request("GET", "/fapi/v1/ticker/bookTicker", params=params)
