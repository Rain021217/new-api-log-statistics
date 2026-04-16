# 兼容性矩阵

## 1. `other` JSON 字段兼容

当前实现已兼容：

1. 缺失 `cache_tokens`
2. 缺失 `cache_creation_tokens`
3. 缺失 `cache_creation_tokens_5m`
4. 缺失 `cache_creation_tokens_1h`
5. 缺失 `model_ratio`
6. 缺失 `completion_ratio`
7. 缺失 `group_ratio`
8. 缺失 `user_group_ratio`

缺失时均按 `0` 或 `1` 回退。

## 2. 固定计费兼容

如果 `model_price > 0`，当前实现按固定计费路径处理，不走按量计费拆分。

## 3. 旧数据兼容

如果旧日志没有缓存字段：

1. 缓存读取成本视为 `0`
2. 缓存写入成本视为 `0`
3. 缓存节省估算视为 `0`

## 4. 货币显示模式兼容

当前支持：

1. `USD`
2. `CNY`
3. `CUSTOM`

其中：

1. `CNY` 使用 `USDExchangeRate`
2. `CUSTOM` 使用 `general_setting.custom_currency_exchange_rate`

## 5. 数据库类型兼容

当前支持：

1. `MySQL`
2. `MariaDB`
3. `PostgreSQL`

其中：

1. `MySQL` / `MariaDB` 支持现有预聚合路径
2. `PostgreSQL` 当前默认走原始统计查询，不启用当前 MySQL 版预聚合刷新脚本
