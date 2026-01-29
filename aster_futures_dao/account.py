from typing import Dict, Any, Optional, List


class AccountDAO:
    """
    Aster Futures 账户DAO
    提供合约账户相关接口
    """
    
    def __init__(self, client):
        self.client = client
    
    def get_balance(self, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        账户余额V2
        
        Args:
            recv_window: 接收窗口时间
        """
        params = {}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v2/balance", params=params, signed=True)
    
    def get_account(self, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        账户信息V2
        
        Args:
            recv_window: 接收窗口时间
        """
        params = {}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v2/account", params=params, signed=True)
    
    def change_leverage(self, symbol: str, leverage: int, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        调整开仓杠杆
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
            recv_window: 接收窗口时间
        """
        params = {
            "symbol": symbol,
            "leverage": leverage
        }
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/leverage", params=params, signed=True)
    
    def change_margin_type(self, symbol: str, margin_type: str, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        变换逐全仓模式
        
        Args:
            symbol: 交易对
            margin_type: 保证金模式 (ISOLATED, CROSSED)
            recv_window: 接收窗口时间
        """
        params = {
            "symbol": symbol,
            "marginType": margin_type
        }
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/marginType", params=params, signed=True)
    
    def adjust_position_margin(self, symbol: str, amount: float, type: int, 
                               position_side: Optional[str] = None, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        调整逐仓保证金
        
        Args:
            symbol: 交易对
            amount: 保证金资金
            type: 调整方向 (1: 增加逐仓保证金, 2: 减少逐仓保证金)
            position_side: 持仓方向 (LONG, SHORT, BOTH)
            recv_window: 接收窗口时间
        """
        params = {
            "symbol": symbol,
            "amount": str(amount),
            "type": type
        }
        if position_side is not None:
            params["positionSide"] = position_side
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("POST", "/fapi/v1/positionMargin", params=params, signed=True)
    
    def get_position_margin_history(self, symbol: str, type: Optional[int] = None, 
                                   start_time: Optional[int] = None, end_time: Optional[int] = None,
                                   limit: Optional[int] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        逐仓保证金变动历史
        
        Args:
            symbol: 交易对
            type: 调整方向 (1: 增加逐仓保证金, 2: 减少逐仓保证金)
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认500
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if type is not None:
            params["type"] = type
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/positionMargin/history", params=params, signed=True)
    
    def get_position_risk(self, symbol: Optional[str] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        用户持仓风险V2
        
        Args:
            symbol: 交易对
            recv_window: 接收窗口时间
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v2/positionRisk", params=params, signed=True)
    
    def get_user_trades(self, symbol: str, order_id: Optional[int] = None, start_time: Optional[int] = None,
                       end_time: Optional[int] = None, from_id: Optional[int] = None, limit: Optional[int] = None,
                       recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        账户成交历史
        
        Args:
            symbol: 交易对
            order_id: 订单号
            start_time: 起始时间
            end_time: 结束时间
            from_id: 起始成交ID
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
        if from_id is not None:
            params["fromId"] = from_id
        if limit is not None:
            params["limit"] = limit
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/userTrades", params=params, signed=True)
    
    def get_income_history(self, symbol: Optional[str] = None, income_type: Optional[str] = None,
                          start_time: Optional[int] = None, end_time: Optional[int] = None,
                          limit: Optional[int] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取账户损益资金流水
        
        Args:
            symbol: 交易对
            income_type: 收益类型 (TRANSFER, WELCOME_BONUS, REALIZED_PNL, FUNDING_FEE, COMMISSION, INSURANCE_CLEAR)
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认500，最大1000
            recv_window: 接收窗口时间
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        if income_type is not None:
            params["incomeType"] = income_type
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/income", params=params, signed=True)
    
    def get_leverage_bracket(self, symbol: Optional[str] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        杠杆分层标准
        
        Args:
            symbol: 交易对
            recv_window: 接收窗口时间
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/leverageBracket", params=params, signed=True)
    
    def get_adl_quantile(self, symbol: Optional[str] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        持仓ADL队列估算
        
        Args:
            symbol: 交易对
            recv_window: 接收窗口时间
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/adlQuantile", params=params, signed=True)
    
    def get_force_orders(self, symbol: Optional[str] = None, auto_close_type: Optional[str] = None,
                        start_time: Optional[int] = None, end_time: Optional[int] = None,
                        limit: Optional[int] = None, recv_window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        用户强平单历史
        
        Args:
            symbol: 交易对
            auto_close_type: 自动平仓类型 (LIQUIDATION, ADL)
            start_time: 起始时间
            end_time: 结束时间
            limit: 限制数量，默认500，最大1000
            recv_window: 接收窗口时间
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        if auto_close_type is not None:
            params["autoCloseType"] = auto_close_type
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/forceOrders", params=params, signed=True)
    
    def get_commission_rate(self, symbol: str, recv_window: Optional[int] = None) -> Dict[str, Any]:
        """
        用户手续费率
        
        Args:
            symbol: 交易对
            recv_window: 接收窗口时间
        """
        params = {"symbol": symbol}
        if recv_window is not None:
            params["recvWindow"] = recv_window
        return self.client.request("GET", "/fapi/v1/commissionRate", params=params, signed=True)
