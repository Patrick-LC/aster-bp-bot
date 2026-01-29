from typing import Dict, Any, Optional, List


class TradeDAO:
    """
    Aster Futures 交易DAO
    提供合约交易相关接口
    """
    
    def __init__(self, client):
        self.client = client
    
    def change_position_side(self, dual_side_position: bool, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        更改持仓模式
        
        Args:
            dual_side_position: True为双向持仓模式，False为单向持仓模式
            recv_window: 接收窗口时间
        """
        params = {"dualSidePosition": str(dual_side_position).lower()}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/positionSide/dual", params=params, signed=True)
    
    def get_position_side(self, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        查询持仓模式
        
        Args:
            recv_window: 接收窗口时间
        """
        params = {}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/positionSide/dual", params=params, signed=True)
    
    def change_multi_assets_margin(self, multi_assets_margin: bool, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        更改联合保证金模式
        
        Args:
            multi_assets_margin: True为开启联合保证金模式，False为关闭
            recv_window: 接收窗口时间
        """
        params = {"multiAssetsMargin": str(multi_assets_margin).lower()}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/multiAssetsMargin", params=params, signed=True)
    
    def get_multi_assets_margin(self, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        查询联合保证金模式
        
        Args:
            recv_window: 接收窗口时间
        """
        params = {}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/multiAssetsMargin", params=params, signed=True)
    
    def place_order(self, symbol: str, side: str, order_type: str, quantity: Optional[float] = None,
                   price: Optional[float] = None, position_side: Optional[str] = None,
                   reduce_only: Optional[bool] = None, new_client_order_id: Optional[str] = None,
                   stop_price: Optional[float] = None, close_position: Optional[bool] = None,
                   activation_price: Optional[float] = None, callback_rate: Optional[float] = None,
                   time_in_force: Optional[str] = None, working_type: Optional[str] = None,
                   price_protect: Optional[bool] = None, new_order_resp_type: Optional[str] = None,
                   recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        下单
        
        Args:
            symbol: 交易对
            side: 买卖方向 (BUY, SELL)
            order_type: 订单类型 (LIMIT, MARKET, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET)
            quantity: 下单数量
            price: 委托价格
            position_side: 持仓方向 (LONG, SHORT, BOTH)
            reduce_only: 是否仅减仓
            new_client_order_id: 用户自定义订单号
            stop_price: 触发价
            close_position: 是否条件全平仓
            activation_price: 追踪止损激活价格
            callback_rate: 追踪止损回调比例
            time_in_force: 有效方法 (GTC, IOC, FOK, GTX, HIDDEN)
            working_type: 条件价格触发类型 (MARK_PRICE, CONTRACT_PRICE)
            price_protect: 条件单触发保护
            new_order_resp_type: 响应类型 (ACK, RESULT)
            recv_window: 接收窗口时间
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type
        }
        
        if quantity is not None:
            params["quantity"] = quantity
        if price is not None:
            params["price"] = price
        if position_side is not None:
            params["positionSide"] = position_side
        if reduce_only is not None:
            params["reduceOnly"] = str(reduce_only).lower()
        if new_client_order_id is not None:
            params["newClientOrderId"] = new_client_order_id
        if stop_price is not None:
            params["stopPrice"] = stop_price
        if close_position is not None:
            params["closePosition"] = str(close_position).lower()
        if activation_price is not None:
            params["activationPrice"] = activation_price
        if callback_rate is not None:
            params["callbackRate"] = callback_rate
        if time_in_force is not None:
            params["timeInForce"] = time_in_force
        if working_type is not None:
            params["workingType"] = working_type
        if price_protect is not None:
            params["priceProtect"] = str(price_protect).upper()
        if new_order_resp_type is not None:
            params["newOrderRespType"] = new_order_resp_type
        if recv_window is not None:
            params["recvWindow"] = recv_window
        
        return self.client.request("POST", "/fapi/v1/order", params=params, signed=True)
    
    def test_order(self, symbol: str, side: str, order_type: str, quantity: Optional[float] = None,
                   price: Optional[float] = None, position_side: Optional[str] = None,
                   reduce_only: Optional[bool] = None, new_client_order_id: Optional[str] = None,
                   stop_price: Optional[float] = None, close_position: Optional[bool] = None,
                   activation_price: Optional[float] = None, callback_rate: Optional[float] = None,
                   time_in_force: Optional[str] = None, working_type: Optional[str] = None,
                   price_protect: Optional[bool] = None, new_order_resp_type: Optional[str] = None,
                   recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        测试下单接口
        参数与place_order相同
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type
        }
        
        if quantity is not None:
            params["quantity"] = quantity
        if price is not None:
            params["price"] = price
        if position_side is not None:
            params["positionSide"] = position_side
        if reduce_only is not None:
            params["reduceOnly"] = str(reduce_only).lower()
        if new_client_order_id is not None:
            params["newClientOrderId"] = new_client_order_id
        if stop_price is not None:
            params["stopPrice"] = stop_price
        if close_position is not None:
            params["closePosition"] = str(close_position).lower()
        if activation_price is not None:
            params["activationPrice"] = activation_price
        if callback_rate is not None:
            params["callbackRate"] = callback_rate
        if time_in_force is not None:
            params["timeInForce"] = time_in_force
        if working_type is not None:
            params["workingType"] = working_type
        if price_protect is not None:
            params["priceProtect"] = str(price_protect).upper()
        if new_order_resp_type is not None:
            params["newOrderRespType"] = new_order_resp_type
        if recv_window is not None:
            params["recvWindow"] = recv_window
        
        return self.client.request("POST", "/fapi/v1/order/test", params=params, signed=True)
    
    def batch_orders(self, batch_orders: List[Dict[str, Any]], recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        批量下单
        
        Args:
            batch_orders: 批量订单列表
            recv_window: 接收窗口时间
        """
        params = {"batchOrders": batch_orders}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/batchOrders", params=params, signed=True)
    
    def transfer(self, asset: str, amount: float, type: int, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        期货现货互转
        
        Args:
            asset: 资产
            amount: 数量
            type: 转账类型 (1: 现货转期货, 2: 期货转现货)
            recv_window: 接收窗口时间
        """
        params = {
            "asset": asset,
            "amount": str(amount),
            "type": type
        }
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/transfer", params=params, signed=True)
    
    def get_order(self, symbol: str, order_id: Optional[int] = None, 
                  orig_client_order_id: Optional[str] = None, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        查询订单
        
        Args:
            symbol: 交易对
            order_id: 系统订单号
            orig_client_order_id: 用户自定义订单号
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/order", params=params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: Optional[int] = None, 
                     orig_client_order_id: Optional[str] = None, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        撤销订单
        
        Args:
            symbol: 交易对
            order_id: 系统订单号
            orig_client_order_id: 用户自定义订单号
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("DELETE", "/fapi/v1/order", params=params, signed=True)
    
    def cancel_all_orders(self, symbol: str, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        撤销全部订单
        
        Args:
            symbol: 交易对
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("DELETE", "/fapi/v1/allOpenOrders", params=params, signed=True)
    
    def batch_cancel_orders(self, symbol: str, order_id_list: Optional[List[int]] = None,
                           orig_client_order_id_list: Optional[List[str]] = None,
                           recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        批量撤销订单
        
        Args:
            symbol: 交易对
            order_id_list: 系统订单号列表
            orig_client_order_id_list: 用户自定义订单号列表
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if order_id_list is not None:
            params["orderIdList"] = order_id_list
        if orig_client_order_id_list is not None:
            params["origClientOrderIdList"] = orig_client_order_id_list
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("DELETE", "/fapi/v1/batchOrders", params=params, signed=True)
    
    def countdown_cancel_all(self, symbol: str, countdown_time: int, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        倒计时撤销所有订单
        
        Args:
            symbol: 交易对
            countdown_time: 倒计时时间（毫秒）
            recv_window: 接收窗口时间
        """
        params = {
            "symbol": symbol,
            "countdownTime": countdown_time
        }
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/countdownCancelAll", params=params, signed=True)
    
    def get_open_order(self, symbol: str, order_id: Optional[int] = None,
                      orig_client_order_id: Optional[str] = None, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        查询当前挂单
        
        Args:
            symbol: 交易对
            order_id: 系统订单号
            orig_client_order_id: 用户自定义订单号
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/openOrder", params=params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查看当前全部挂单
        
        Args:
            symbol: 交易对
            recv_window: 接收窗口时间
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/openOrders", params=params, signed=True)
    
    def get_all_orders(self, symbol: str, order_id: Optional[int] = None, start_time: Optional[int] = None,
                      end_time: Optional[int] = None, limit: Optional[int] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询所有订单（包括历史订单）
        
        Args:
            symbol: 交易对
            order_id: 系统订单号
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认500，最大1000
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/allOrders", params=params, signed=True)
