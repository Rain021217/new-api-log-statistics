`new-api-log-statistics` `v0.1.0` 是首个可公开发布版本，提供面向 `new-api` 日志数据库的独立日志账单统计与分析面板。

## 本版包含

- 支持按时间范围、令牌、模型、用户、分组、渠道、Request ID、IP 进行筛选统计
- 支持输入、输出、缓存读取、缓存创建的 Token 与费用拆分统计
- 支持摘要卡、趋势图、排行图、成本构成图、缓存节省估算
- 支持明细分页、排序、列显隐
- 支持 `CSV`、`XLSX`、图表 `PNG` 导出
- 支持多数据源接入
- 支持可选 `Redis` 查询缓存
- 支持可选登录鉴权

## 部署与分发

- 提供 `Docker` 与 `Docker Compose` 部署方式
- 提供初始化脚本、冒烟脚本、发布打包脚本
- 提供面向 GitHub 上传的干净仓库导出目录

## 发布说明

- 用户发布包不包含本地 `.env`
- 用户发布包不包含真实 `config/sources.yml`
- 用户发布包不包含运行日志与内部阶段文档
- 如需启用登录门禁，请在 `.env` 中配置 `AUTH_ENABLED`、`AUTH_USERNAME`、`AUTH_PASSWORD`、`AUTH_SESSION_SECRET`

## 建议下载

- 最终用户部署：下载 `new-api-log-statistics-0.1.0.tar.gz`
- 仓库维护与二次开发：使用 GitHub 仓库源码或 GitHub-ready 导出目录
