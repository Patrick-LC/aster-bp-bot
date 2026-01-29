# BP + Aster合约对冲策略脚本

## 概述

`hedge_bp_aster_futures_loop.py` 是一个自动化对冲交易脚本，实现了以下策略：

1. **第一腿**: 在Backpack上做空ASTER，同时在Aster合约上做多对冲
2. **第二腿**: 在Backpack上做多ASTER，同时在Aster合约上做空对冲

## 主要特性

- **合约对冲**: 使用Aster合约API进行对冲交易
- **智能监控**: 持续监控BP订单状态，自动重挂未成交订单
- **资金费率管理**: 自动检测资金费率时间，避免在费率结算前后交易
- **错误处理**: 完善的错误处理和重试机制
- **实时日志**: 详细的交易日志和状态监控

## 使用方法

### 1. 配置文件

复制并修改配置文件：

```bash
cp config/hedge_futures.example.yaml config/hedge_futures.yaml
```

编辑 `config/hedge_futures.yaml`：

```yaml
bp:
  api_public_key_b64: "YOUR_BP_PUBLIC_KEY_BASE64"
  api_secret_key_b64: "YOUR_BP_SECRET_KEY_BASE64"
  base_url: "https://api.backpack.exchange"
  symbol: "ASTER_USDC_PERP"
  window: 5000
  debug: true

aster:
  api_key: "YOUR_ASTER_API_KEY"
  api_secret: "YOUR_ASTER_API_SECRET"
  base_url: "https://fapi.asterdex.com"
  symbol: "ASTERUSDT"
  recv_window: 5000
  debug: false

trade:
  quantity: "10"                    # 交易数量
  offset_percent: 0.2              # 价格偏移百分比
  first_wait_seconds: 10           # 第一腿等待时间
  between_legs_sleep: 20           # 两腿之间等待时间
  stop_before_funding_minutes: 5   # 资金费率前停止交易分钟数
  cycle_sleep: 60                  # 每轮循环间隔秒数
```

### 2. 运行脚本

```bash
python scripts/hedge_bp_aster_futures_loop.py config/hedge_futures.yaml
```

## 策略逻辑

### 第一腿：BP做空 + Aster合约做多

1. 获取BP最新价格
2. 计算做空价格（最新价 + 0.2%）
3. 在BP上下限价做空订单
4. 持续监控订单状态
5. 如果10秒内未成交，取消订单并重新挂单
6. 订单成交后，立即在Aster合约上做多对冲

### 第二腿：BP做多 + Aster合约做空

1. 获取BP最新价格
2. 计算做多价格（最新价 - 0.2%）
3. 在BP上下限价做多订单
4. 持续监控订单状态
5. 如果10秒内未成交，取消订单并重新挂单
6. 订单成交后，立即在Aster合约上做空对冲

## 资金费率管理

脚本会自动检测资金费率时间（每8小时一次：00:00, 08:00, 16:00 UTC），并在费率结算前停止交易，避免额外的资金费用。

## 监控和日志

脚本提供详细的日志输出：

- 订单状态监控
- 价格计算过程
- 对冲执行结果
- 错误和异常信息
- 资金费率时间提醒

## 注意事项

1. **API权限**: 确保API密钥具有交易权限
2. **资金充足**: 确保账户有足够的资金进行对冲
3. **网络稳定**: 建议在稳定的网络环境下运行
4. **风险控制**: 建议设置合理的交易数量和价格偏移
5. **监控运行**: 建议定期检查脚本运行状态

## 错误处理

脚本包含完善的错误处理机制：

- 网络连接错误自动重试
- 订单状态查询失败处理
- 404错误（订单可能已成交）处理
- 异常情况下的安全退出

## 配置参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| quantity | 交易数量 | "10" |
| offset_percent | 价格偏移百分比 | 0.2 |
| first_wait_seconds | 第一腿等待时间 | 10 |
| between_legs_sleep | 两腿之间等待时间 | 20 |
| stop_before_funding_minutes | 资金费率前停止交易分钟数 | 5 |
| cycle_sleep | 每轮循环间隔秒数 | 60 |

## 示例输出

```
[Cycle 1] 开始新一轮对冲策略
[Cycle 1] 距离资金费率时间 16:00 UTC 还有 120分钟

[Cycle 1] 开始执行对冲策略
[Leg1] BP 限价做空价: 1.7234 (基于最新价 1.72)，symbol=ASTER_USDC_PERP
[Leg1] BP 做空下单回执: [{'orderId': '10016317016', 'status': 'New', ...}]
[Leg1] 开始监控 BP 做空订单 10016317016，将持续监控直到成交...
[Leg1] BP 做空订单 10016317016 已成交！总耗时 3 秒，状态: FILLED
[Leg1] BP 做空已成交，ASTER合约 市价买入对冲...
[Leg1] ASTER合约 市价买入回执: {'orderId': 12345, 'status': 'FILLED', ...}

休眠 20 秒...

[Leg2] BP 限价做多价: 1.7166 (基于最新价 1.72)，symbol=ASTER_USDC_PERP
[Leg2] BP 做多下单回执: [{'orderId': '10016317017', 'status': 'New', ...}]
[Leg2] 开始监控 BP 做多订单 10016317017，将持续监控直到成交...
[Leg2] BP 做多订单 10016317017 已成交！总耗时 2 秒，状态: FILLED
[Leg2] BP 做多已成交，ASTER合约 市价卖出对冲...
[Leg2] ASTER合约 市价卖出回执: {'orderId': 12346, 'status': 'FILLED', ...}

[Cycle 1] 完成，等待 60 秒后开始下一轮...
```

## 故障排除

### 常见问题

1. **API密钥错误**: 检查配置文件中的API密钥是否正确
2. **网络连接失败**: 检查网络连接和防火墙设置
3. **订单未成交**: 检查价格偏移设置是否合理
4. **权限不足**: 确保API密钥具有交易权限

### 调试模式

启用调试模式获取更详细的日志：

```yaml
bp:
  debug: true
aster:
  debug: true
```

## 安全建议

1. 定期备份配置文件
2. 使用专用的交易账户
3. 设置合理的交易限额
4. 监控账户资金变化
5. 定期检查脚本运行状态
