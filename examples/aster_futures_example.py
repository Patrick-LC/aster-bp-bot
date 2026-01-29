#!/usr/bin/env python3
"""
Aster Futures API 使用示例
演示如何使用 aster_futures_dao 进行合约交易
"""

import sys
import time
from pathlib import Path

# 确保导入本地包
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aster_futures_dao.http import AsterFuturesClient
from aster_futures_dao.market import MarketDataDAO
from aster_futures_dao.trade import TradeDAO
from aster_futures_dao.account import AccountDAO
from aster_futures_dao.ws import AsterFuturesWS


def main():
    """主函数"""
    print("Aster Futures API 示例")
    print("=" * 50)
    
    # 配置（请替换为您的实际API密钥）
    api_key = "YOUR_API_KEY"
    api_secret = "YOUR_API_SECRET"
    
    # 创建客户端
    client = AsterFuturesClient(
        api_key=api_key,
        api_secret=api_secret,
        debug=True
    )
    
    # 创建DAO实例
    market = MarketDataDAO(client)
    trade = TradeDAO(client)
    account = AccountDAO(client)
    
    try:
        # 1. 测试连接
        print("\n1. 测试连接...")
        ping_result = market.ping()
        print(f"Ping结果: {ping_result}")
        
        # 2. 获取服务器时间
        print("\n2. 获取服务器时间...")
        time_result = market.time()
        print(f"服务器时间: {time_result}")
        
        # 3. 获取交易对信息
        print("\n3. 获取交易对信息...")
        exchange_info = market.exchange_info()
        print(f"交易对数量: {len(exchange_info.get('symbols', []))}")
        
        # 4. 获取BTCUSDT价格
        print("\n4. 获取BTCUSDT价格...")
        ticker = market.ticker_price("BTCUSDT")
        print(f"BTCUSDT价格: {ticker}")
        
        # 5. 获取账户余额（需要有效API密钥）
        print("\n5. 获取账户余额...")
        try:
            balance = account.get_balance()
            print(f"账户余额: {balance}")
        except Exception as e:
            print(f"获取账户余额失败: {e}")
        
        # 6. 获取持仓信息
        print("\n6. 获取持仓信息...")
        try:
            positions = account.get_position_risk()
            print(f"持仓信息: {positions}")
        except Exception as e:
            print(f"获取持仓信息失败: {e}")
        
        # 7. WebSocket示例
        print("\n7. WebSocket示例...")
        ws = AsterFuturesWS(debug=True)
        
        def on_ticker(data):
            print(f"收到ticker数据: {data}")
        
        def on_depth(data):
            print(f"收到深度数据: {data}")
        
        # 订阅BTCUSDT的ticker和深度数据
        ws.subscribe_ticker("BTCUSDT", on_ticker)
        ws.subscribe_depth("BTCUSDT", on_depth)
        
        # 连接WebSocket
        ws.connect()
        
        # 等待一些数据
        print("等待WebSocket数据...")
        time.sleep(5)
        
        # 断开连接
        ws.disconnect()
        
    except Exception as e:
        print(f"发生错误: {e}")
    
    print("\n示例完成!")


if __name__ == "__main__":
    main()
