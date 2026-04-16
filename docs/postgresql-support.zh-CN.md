# PostgreSQL 支持说明

## 1. 当前支持范围

当前版本已经为以下能力增加 PostgreSQL 一等支持：

1. 数据源创建、保存、编辑
2. 连接测试
3. 健康检查
4. 元数据接口
5. 统计汇总
6. 分页明细
7. 趋势与 breakdown
8. 图表接口
9. CSV / XLSX 导出

支持的 `db_type`：

1. `mysql`
2. `mariadb`
3. `postgres`

## 2. 接入方式

### 2.1 手工新增

前端“数据源接入”里的“五元组新增”已经支持选择：

1. `MySQL`
2. `MariaDB`
3. `PostgreSQL`

当选择 `PostgreSQL` 时，端口建议使用 `5432`。

### 2.2 URI 导入

当前支持：

1. `postgres://user:password@host:5432/new-api`
2. `postgresql://user:password@host:5432/new-api`

## 3. 兼容假设

当前 PostgreSQL 支持基于以下假设：

1. 业务表语义与 MySQL 版 `new-api` 等价
2. 至少存在：
   - `logs`
   - `options`
   - `tokens`
   - `channels`
3. `logs.other` 可被解释为 `json/jsonb` 或合法 JSON 文本
4. `created_at` 仍然是 Unix 时间戳字段

## 4. 已完成的方言适配

当前已经处理的 PostgreSQL / MySQL 方言差异包括：

1. JSON 提取
2. 保留字字段 `group`
3. `key/value` 列引用
4. 数值转换
5. 时间分桶
6. 时间戳格式化
7. `information_schema` 探测
8. 连接与字典行结果兼容

## 5. 当前限制

### 5.1 预聚合

PostgreSQL 当前默认走原始趋势查询，不启用预聚合表刷新。

也就是说：

1. PostgreSQL 统计接口可正常使用
2. 长时间范围查询不会自动走当前的 MySQL 版聚合表逻辑
3. `refresh_daily_aggregates.py` 目前仍按 MySQL 路径设计

这是有意的保守实现，优先保证主查询链路可用，不在未确认表结构前贸然对 PostgreSQL 执行建表和刷新逻辑。

### 5.2 `logs.other`

如果 PostgreSQL 中 `logs.other` 不是合法 JSON 文本，也不是 `json/jsonb`，则当前统计 SQL 不能正确提取其中的成本参数。

## 6. 排查建议

如果 PostgreSQL 数据源能连通但查不到统计数据，优先检查：

1. `db_type` 是否真的设为 `postgres`
2. 端口是否为 `5432`
3. `logs` 表是否存在并且 `type = 2` 有数据
4. `logs.other` 是否包含：
   - `model_ratio`
   - `completion_ratio`
   - `cache_ratio`
   - `group_ratio`
   - `user_group_ratio`
5. `options` 表是否存在并包含：
   - `QuotaPerUnit`
   - `USDExchangeRate`
   - `general_setting.quota_display_type`

## 7. 对当前项目的实际提示

如果某个第三方数据源：

1. 端口是 `5432`
2. 但当前配置里 `db_type` 仍是 `mysql`

那它即使网络可达，也会被错误地按 MySQL 驱动连接，导致无法拉取统计数据。
