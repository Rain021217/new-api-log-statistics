`new-api-log-statistics` `v0.2.0` 是首个包含 PostgreSQL 一等支持的数据发布版本。

## 本版新增

- 为 `MySQL` / `MariaDB` / `PostgreSQL` 提供统一的数据源管理能力
- 新增 PostgreSQL 数据源连接测试、健康检查、元数据查询、汇总、明细、趋势、breakdown、图表与导出支持
- 新增前端删除数据源能力
- 新增 PostgreSQL 兼容说明与接入文档

## 本版保留

- `Docker` 与 `Docker Compose` 部署方式
- `CSV` / `XLSX` / 图表 `PNG` 导出
- 多数据源接入
- 可选 `Redis` 查询缓存
- 可选登录鉴权

## 发布说明

- 用户发布包不包含本地 `.env`
- 用户发布包不包含真实 `config/sources.yml`
- 用户发布包不包含运行日志与内部阶段文档
- 如需启用登录门禁，请在 `.env` 中配置 `AUTH_ENABLED`、`AUTH_USERNAME`、`AUTH_PASSWORD`、`AUTH_SESSION_SECRET`

## 建议下载

- 最终用户部署：下载 `new-api-log-statistics-0.2.0.tar.gz`
- 仓库维护与二次开发：使用 GitHub 仓库源码或 GitHub-ready 导出目录
