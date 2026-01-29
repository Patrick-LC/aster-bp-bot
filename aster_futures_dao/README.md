# Aster Futures DAO

Aster合约交易API的Python DAO封装，提供简洁易用的接口进行合约交易。

## 功能特性

- **HTTP客户端**: 支持Aster合约API的HTTP请求和签名
- **市场数据**: 获取价格、深度、K线等市场数据
- **交易功能**: 下单、撤单、查询订单等交易操作
- **账户管理**: 查询余额、持仓、资金流水等账户信息
- **WebSocket**: 实时数据流订阅，支持ticker、深度、交易等数据

## 安装依赖

```bash
pip install requests websocket-client PyYAML PyNaCl
```

## 快速开始

### 1. 基本使用

```python
from aster_futures_dao.http import AsterFuturesClient
from aster_futures_dao.market import MarketDataDAO
from aster_futures_dao.trade import TradeDAO

# 创建客户端
client = AsterFuturesClient(
    api_key="your_api_key",
    api_secret="your_api_secret",
    debug=True
)

# 创建DAO实例
market = MarketDataDAO(client)
trade = TradeDAO(client)

# 获取价格
ticker = market.ticker_price("BTCUSDT")
print(f"BTCUSDT价格: {ticker}")

# 下单
order = trade.place_order(
    symbol="BTCUSDT",
    side="BUY",
    order_type="MARKET",
    quantity=0.001
)
print(f"订单结果: {order}")
```

### 2. WebSocket实时数据

```python
from aster_futures_dao.ws import AsterFuturesWS

# 创建WebSocket客户端
ws = AsterFuturesWS(debug=True)

# 定义数据处理函数
def on_ticker(data):
    print(f"收到ticker数据: {data}")

def on_depth(data):
    print(f"收到深度数据: {data}")

# 订阅数据流
ws.subscribe_ticker("BTCUSDT", on_ticker)
ws.subscribe_depth("BTCUSDT", on_depth)

# 连接并开始接收数据
ws.connect()
```

## API参考

### HTTP客户端 (AsterFuturesClient)

- `__init__(api_key, api_secret, base_url, debug)`: 初始化客户端
- `request(method, path, params, signed)`: 发送HTTP请求

### 市场数据 (MarketDataDAO)

- `ping()`: 测试连接
- `time()`: 获取服务器时间
- `exchange_info()`: 获取交易规则和交易对信息
- `ticker_price(symbol)`: 获取最新价格
- `ticker_24hr(symbol)`: 获取24hr价格变动
- `depth(symbol, limit)`: 获取深度信息
- `klines(symbol, interval, ...)`: 获取K线数据
- `premium_index(symbol)`: 获取标记价格和资金费率

### 交易功能 (TradeDAO)

- `place_order(symbol, side, order_type, ...)`: 下单
- `cancel_order(symbol, order_id)`: 撤单
- `get_order(symbol, order_id)`: 查询订单
- `get_open_orders(symbol)`: 查询当前挂单
- `get_all_orders(symbol, ...)`: 查询所有订单
- `change_leverage(symbol, leverage)`: 调整杠杆
- `change_margin_type(symbol, margin_type)`: 调整保证金模式

### 账户管理 (AccountDAO)

- `get_balance()`: 获取账户余额
- `get_account()`: 获取账户信息
- `get_position_risk(symbol)`: 获取持仓风险
- `get_user_trades(symbol, ...)`: 获取成交历史
- `get_income_history(symbol, ...)`: 获取资金流水

### WebSocket (AsterFuturesWS)

- `connect()`: 连接WebSocket
- `disconnect()`: 断开连接
- `subscribe_ticker(symbol, handler)`: 订阅ticker数据
- `subscribe_depth(symbol, handler)`: 订阅深度数据
- `subscribe_trades(symbol, handler)`: 订阅交易数据
- `subscribe_kline(symbol, interval, handler)`: 订阅K线数据

## 配置示例

```yaml
aster:
  api_key: "your_api_key"
  api_secret: "your_api_secret"
  base_url: "https://fapi.asterdex.com"
  symbol: "ASTERUSDT"
  recv_window: 5000
  debug: false
```

## 注意事项

1. **API密钥安全**: 请妥善保管您的API密钥，不要泄露给他人
2. **权限设置**: 确保API密钥具有相应的交易权限
3. **频率限制**: 注意API调用频率限制，避免被限制访问
4. **错误处理**: 建议在生产环境中添加适当的错误处理逻辑
5. **WebSocket重连**: WebSocket连接可能因网络问题断开，建议实现自动重连机制

## 示例脚本

查看 `examples/aster_futures_example.py` 获取完整的使用示例。

## 更新日志

- v1.0.0: 初始版本，支持基本的合约交易功能
