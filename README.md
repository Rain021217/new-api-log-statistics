# new-api-log-statistics

[![Release](https://img.shields.io/github/v/release/Rain021217/new-api-log-statistics?display_name=tag)](https://github.com/Rain021217/new-api-log-statistics/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/Rain021217/new-api-log-statistics/ci.yml?branch=main)](https://github.com/Rain021217/new-api-log-statistics/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/Rain021217/new-api-log-statistics)](./LICENSE)

`new-api-log-statistics` 是一个面向 `new-api` 日志数据库的独立统计与账单分析面板，提供筛选、汇总、图表、分页明细、CSV/XLSX 导出、多数据源接入，以及可选 Redis 缓存与登录鉴权。

适合用于：

- 令牌成本分析
- 模型与渠道对账
- 缓存命中收益观察
- `new-api` 日志账单复盘

## 快速入口

- 最新发布：<https://github.com/Rain021217/new-api-log-statistics/releases/latest>
- 用户部署说明：[`README.md`](./README.md)
- 维护者发布说明：[`docs/maintainer-publishing.zh-CN.md`](./docs/maintainer-publishing.zh-CN.md)
- Release Notes：[`docs/release-notes-v0.2.0.md`](./docs/release-notes-v0.2.0.md)

这个仓库同时支持两种使用方式：

1. `Docker Compose` 一键部署
2. 仅用 `Docker` 构建单容器运行

发布版默认不包含你的本地数据库配置、运行日志、阶段文档和临时验证文件。请使用示例配置完成初始化。

## 1. 功能概览

- 按时间范围、令牌、模型、用户、分组、渠道、Request ID、IP 筛选
- 统计输入、输出、缓存读取、缓存创建的 Token 与费用
- 汇总卡片展示总请求数、总 Token、总花费、平均 RPM、平均 TPM
- 明细表分页、排序、列显隐
- 趋势图、分布图、缓存节省估算
- `CSV`、`XLSX`、图表 `PNG` 导出
- 多数据源管理
- 可选 `Redis` 查询缓存
- 原生支持 `MySQL` / `MariaDB` / `PostgreSQL` 数据源

## 2. 目录说明

发布版保留的核心目录如下：

- `app/`
  后端服务源码，基于 `FastAPI`
- `web/`
  前端静态页面
- `deploy/`
  `Dockerfile`、`docker-compose.yml`、`nginx.conf`
- `config/`
  只保留示例数据源配置
- `scripts/`
  初始化脚本、发布打包脚本、发布校验脚本
- `runtime/`
  运行日志目录，发布包中默认为空

根目录的发布辅助文件如下：

- `LICENSE`
  开源许可证
- `CHANGELOG.md`
  版本变更记录
- `CONTRIBUTING.md`
  贡献约定
- `SECURITY.md`
  安全与私有信息处理约定

## 3. 环境要求

开始前请确认本机已安装：

1. `Docker 24+`
2. `Docker Compose v2`
3. 可访问目标 `new-api` 数据库的网络权限

检查命令：

```bash
docker --version
docker compose version
```

## 4. 快速开始

### 4.1 下载并进入项目目录

```bash
cd /path/to/new-api-log-statistics
```

### 4.2 初始化配置文件

首次部署前先生成本地可编辑配置：

```bash
make init-config
```

这条命令会做三件事：

1. 如果根目录没有 `.env`，就从 `.env.example` 复制一份
2. 如果 `config/sources.yml` 不存在，就从 `config/sources.example.yml` 复制一份
3. 如果 `runtime/` 不存在，就自动创建

### 4.3 编辑 `.env`

打开根目录 `.env`，逐行确认下面这些参数。

```dotenv
APP_TITLE=new-api-log-statistics
APP_VERSION=0.2.0
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=18080
NGINX_PORT=18090
TZ=Asia/Shanghai
LOG_LEVEL=INFO
QUERY_CACHE_TTL=300
DB_POOL_SIZE=4
REQUEST_TIMEOUT_SECONDS=5
SLOW_QUERY_THRESHOLD_MS=250
ALLOW_REMOTE_DB=true
REDIS_URL=
ENABLE_LOCAL_IMPORT=false
STARTUP_VALIDATE_SOURCES=true
LOCAL_IMPORT_SCAN_ROOTS=/app
LOCAL_IMPORT_MAX_DEPTH=3
SOURCE_CONFIG_PATH=/app/config/sources.yml
APP_LOG_PATH=/app/runtime/app.log
ACCESS_LOG_PATH=/app/runtime/access.log
AUDIT_LOG_PATH=/app/runtime/audit.log
```

参数解释如下。

- `APP_TITLE`
  页面和接口返回的服务名称，通常不需要改
- `APP_VERSION`
  应用版本号，通常不需要改
- `APP_ENV`
  运行环境标记。开发环境可用 `development`，生产可改成 `production`
- `APP_HOST`
  容器内监听地址，保持 `0.0.0.0` 即可
- `APP_PORT`
  宿主机映射到后端应用的端口。默认是 `18080`
- `NGINX_PORT`
  宿主机映射到 `Nginx` 入口的端口。默认是 `18090`
- `TZ`
  时区，默认 `Asia/Shanghai`
- `LOG_LEVEL`
  应用日志级别，可选 `DEBUG`、`INFO`、`WARNING`、`ERROR`
- `QUERY_CACHE_TTL`
  查询缓存时间，单位秒
- `DB_POOL_SIZE`
  每个数据源的数据库连接池大小
- `REQUEST_TIMEOUT_SECONDS`
  单次数据库请求超时时间，单位秒
- `SLOW_QUERY_THRESHOLD_MS`
  超过这个毫秒数就记为慢查询
- `ALLOW_REMOTE_DB`
  是否允许连接远程数据库。通常保持 `true`
- `REDIS_URL`
  Redis 地址。为空表示不用 Redis，例如 `redis://redis:6379/0`
- `ENABLE_LOCAL_IMPORT`
  是否允许扫描本机 `new-api` 配置并尝试导入数据源
- `STARTUP_VALIDATE_SOURCES`
  服务启动时是否自动校验已启用数据源
- `LOCAL_IMPORT_SCAN_ROOTS`
  本机扫描模式下允许扫描的根目录
- `LOCAL_IMPORT_MAX_DEPTH`
  本机扫描的最大目录深度
- `SOURCE_CONFIG_PATH`
  容器内数据源配置文件路径，保持默认即可
- `AUTH_ENABLED`
  是否启用可选登录鉴权。设置为 `true` 后，除根页面、静态资源、鉴权接口和可选健康检查外，其余接口都需要先登录
- `AUTH_USERNAME`
  登录用户名
- `AUTH_PASSWORD`
  登录密码。只要 `AUTH_ENABLED=true`，这个字段就必须设置，否则服务会在启动时直接报错
- `AUTH_SESSION_SECRET`
  用于签名登录 Cookie 的密钥。生产环境必须改掉默认值
- `AUTH_SESSION_COOKIE`
  登录 Cookie 名称
- `AUTH_SESSION_MAX_AGE`
  登录会话有效期，单位秒
- `AUTH_COOKIE_SECURE`
  是否只允许通过 HTTPS 发送 Cookie。公网 HTTPS 部署时建议设为 `true`
- `AUTH_ALLOW_BASIC`
  是否允许用 HTTP Basic Auth 访问 API，适合脚本或反代场景
- `AUTH_PUBLIC_HEALTH`
  是否允许 `GET /api/health` 在未登录时直接访问
- `APP_LOG_PATH`
  应用日志文件路径
- `ACCESS_LOG_PATH`
  访问日志文件路径
- `AUDIT_LOG_PATH`
  审计日志文件路径

如果端口冲突，可以直接修改下面两行：

```dotenv
APP_PORT=28080
NGINX_PORT=28090
```

### 4.4 启用可选登录鉴权

如果你准备把这个服务部署在共享网络、跳板机或带公网入口的环境，建议启用登录门禁。

在 `.env` 里增加或修改下面这些值：

```dotenv
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD=replace_with_a_strong_password
AUTH_SESSION_SECRET=replace_with_a_long_random_secret
AUTH_SESSION_MAX_AGE=43200
AUTH_COOKIE_SECURE=false
AUTH_ALLOW_BASIC=true
AUTH_PUBLIC_HEALTH=true
```

建议这样理解：

- `AUTH_PASSWORD`
  这是网页登录密码，也是 Basic Auth 的密码
- `AUTH_SESSION_SECRET`
  这是 Cookie 签名密钥，不要和登录密码写成一样
- `AUTH_COOKIE_SECURE=true`
  只有在你前面已经上了 HTTPS 反向代理时再打开

启用后：

1. 根页面仍可打开
2. 页面会先显示登录卡片
3. 登录后才会加载数据源、统计、导出等受保护内容
4. API 脚本也可以使用 Basic Auth 直接访问

## 5. 配置数据源

### 5.1 编辑 `config/sources.yml`

初始化后，编辑下面这个文件：

```yaml
sources:
  - source_id: demo-mysql
    source_name: Demo MySQL
    db_type: mysql
    host: 127.0.0.1
    port: 3306
    user: newapi_stats
    password: change_me
    database: new-api
    charset: utf8mb4
    timezone: Asia/Shanghai
    enabled: true
    readonly: true
    schema_version_hint: ""
    notes: "Example source. Replace host/user/password/database with your own values."
```

每个字段的填写方法如下。

- `source_id`
  数据源唯一标识，只能使用稳定的英文、数字、连字符。示例：`prod-main`
- `source_name`
  页面上显示的数据源名称。示例：`生产主库`
- `db_type`
  数据库类型，目前填写 `mysql`、`mariadb` 或 `postgres`
- `host`
  数据库主机名或 IP
- `port`
  数据库端口，MySQL / MariaDB 默认 `3306`，PostgreSQL 默认 `5432`
- `user`
  只读数据库用户名
- `password`
  只读数据库密码
- `database`
  `new-api` 使用的数据库名，常见是 `new-api`
- `charset`
  MySQL / MariaDB 一般保持 `utf8mb4`，PostgreSQL 可以留空
- `timezone`
  一般保持 `Asia/Shanghai`
- `enabled`
  是否启用这个数据源
- `readonly`
  建议保持 `true`
- `schema_version_hint`
  兼容提示用，可留空
- `notes`
  备注信息，可留空

### 5.2 一个完整的生产示例

```yaml
sources:
  - source_id: prod-main
    source_name: Production Main
    db_type: mysql
    host: 10.0.0.12
    port: 3306
    user: newapi_readonly
    password: your_password_here
    database: new-api
    charset: utf8mb4
    timezone: Asia/Shanghai
    enabled: true
    readonly: true
    schema_version_hint: ""
    notes: "Primary read-only analytics source."
```

### 5.3 PostgreSQL 示例

```yaml
sources:
  - source_id: prod-pg
    source_name: Production PostgreSQL
    db_type: postgres
    host: 10.0.0.23
    port: 5432
    user: newapi_readonly
    password: your_password_here
    database: new-api
    charset: ""
    timezone: Asia/Shanghai
    enabled: true
    readonly: true
    schema_version_hint: ""
    notes: "PostgreSQL read-only analytics source."
```

补充说明：

- PostgreSQL 推荐使用 `db_type: postgres`
- PostgreSQL URI 导入支持 `postgres://` 和 `postgresql://`
- PostgreSQL 不使用 `charset` 参数建立连接，留空即可

## 6. 如何获取数据库连接信息

你至少需要下面 5 个参数：

1. 数据库地址
2. 数据库端口
3. 数据库名
4. 只读用户名
5. 只读密码

最推荐的做法是让 `new-api` 所在机器的运维或 DBA 创建一个只读账号，只授予这些表的 `SELECT` 权限：

1. `logs`
2. `options`
3. `tokens`
4. `channels`

### 6.1 如果你拿到的是数据库 URL

常见格式如下：

```text
mysql://username:password@db.example.com:3306/new-api
mysql+pymysql://username:password@db.example.com:3306/new-api?charset=utf8mb4
```

你可以拆成这几个部分：

- `username`
  对应 `user`
- `password`
  对应 `password`
- `db.example.com`
  对应 `host`
- `3306`
  对应 `port`
- `new-api`
  对应 `database`

也可以直接在网页里使用“URI 导入”。

### 6.2 如果你不知道数据库 URL 在哪里

按这个顺序排查。

1. 查看 `new-api` 项目的 `.env`
2. 查看 `docker-compose.yml`、`compose.yaml` 或部署平台的环境变量页
3. 查看容器启动参数或托管面板里的环境变量
4. 向部署方或 DBA 索取“数据库地址、端口、库名、只读账号、只读密码”

如果你的 `new-api` 是通过 Docker 部署的，可以先尝试：

```bash
docker compose config
docker inspect <new-api-container-name>
```

如果是 Linux 主机上的普通部署，可以先查看：

```bash
cat .env
cat docker-compose.yml
cat compose.yaml
```

如果服务已经在跑，但你不知道配置文件在哪里，可以先找可能的部署目录：

```bash
find /opt /srv /data /home -maxdepth 4 -type f \( -name ".env" -o -name "docker-compose.yml" -o -name "compose.yaml" \)
```

### 6.3 如果你只拿到“主机、库名、账号、密码”

那就直接填 `config/sources.yml`，不需要额外转换。

## 7. 使用 Docker Compose 部署

### 7.1 不启用 Redis

```bash
make init-config
make build
make up
make health
```

等价命令：

```bash
docker compose --env-file .env -f deploy/docker-compose.yml build
docker compose --env-file .env -f deploy/docker-compose.yml up -d
curl -s http://127.0.0.1:18080/api/health
curl -s http://127.0.0.1:18090/api/health
```

### 7.2 启用 Redis 缓存

先把 `.env` 里的 `REDIS_URL` 改成：

```dotenv
REDIS_URL=redis://redis:6379/0
```

然后运行：

```bash
make init-config
make build
make up-cache
make health
```

等价命令：

```bash
docker compose --env-file .env -f deploy/docker-compose.yml build
docker compose --env-file .env -f deploy/docker-compose.yml --profile cache up -d
curl -s http://127.0.0.1:18080/api/health
curl -s http://127.0.0.1:18090/api/health
```

### 7.3 查看状态和日志

```bash
make ps
make logs
```

停止服务：

```bash
make down
```

## 8. 使用 Docker 单独运行

如果你不想用 `docker compose`，可以只构建应用镜像。

### 8.1 构建镜像

```bash
docker build -t new-api-log-statistics:local -f deploy/Dockerfile .
```

### 8.2 运行容器

先确保你已经准备好了：

1. `.env`
2. `config/sources.yml`
3. `runtime/`

运行命令：

```bash
docker run -d \
  --name new-api-log-statistics \
  --env-file .env \
  -p 18080:8080 \
  -v "$(pwd)/config:/app/config" \
  -v "$(pwd)/runtime:/app/runtime" \
  new-api-log-statistics:local
```

如果要额外走 `Nginx` 反代，请自行配置外层代理到 `18080`。

## 9. 启动后如何使用

### 9.1 打开页面

默认入口：

- `http://127.0.0.1:18090`
- 如果没启 `nginx`，也可以直接访问 `http://127.0.0.1:18080`

如果启用了 `AUTH_ENABLED=true`，页面会先要求输入账号密码，登录成功后才会显示数据源和统计结果。

### 9.2 首次检查

先看页面顶部两个区域：

1. 服务状态是否为正常
2. 已配置数据源是否显示你在 `config/sources.yml` 里填写的数据源

如果没有显示，先检查：

```bash
cat config/sources.yml
docker compose --env-file .env -f deploy/docker-compose.yml ps
docker compose --env-file .env -f deploy/docker-compose.yml logs -f app
```

### 9.3 查询日志成本

在“统计查询”区域可以填写：

- 数据源
- 令牌名称
- 模型名称
- 用户名
- 分组
- 渠道 ID
- Request ID
- IP
- 开始时间
- 结束时间

点击“查询”后，你会得到：

1. 摘要卡片
2. 趋势图和构成图
3. 分页明细表
4. CSV/XLSX 导出链接

## 10. 常见问题

### 10.1 页面能打开，但没有数据源

按顺序检查：

```bash
ls -la config
cat config/sources.yml
docker compose --env-file .env -f deploy/docker-compose.yml logs app
curl -s http://127.0.0.1:18080/api/sources
```

### 10.2 端口冲突

修改 `.env`：

```dotenv
APP_PORT=28080
NGINX_PORT=28090
```

然后重启：

```bash
make down
make up
```

### 10.3 数据库连不上

优先检查：

1. `host`、`port`、`database` 是否正确
2. 用户名密码是否正确
3. 目标数据库是否允许当前机器访问
4. 只读账号是否至少有 `logs/options/tokens/channels` 的 `SELECT`

### 10.4 费用是负数

当前版本已经兼容 `new-api` 中 `user_group_ratio = -1` 的语义，并自动回退到 `group_ratio`。如果你仍看到负值，请优先检查这条日志的 `other` JSON 是否被第三方插件篡改。

### 10.5 启用了鉴权但无法登录

优先检查：

1. `.env` 中是否真的设置了 `AUTH_ENABLED=true`
2. 是否同时设置了 `AUTH_PASSWORD`
3. `AUTH_SESSION_SECRET` 是否仍是默认占位值
4. 如果你走 HTTPS 反代，`AUTH_COOKIE_SECURE` 是否与实际协议匹配
5. 如果是脚本访问 API，`Authorization: Basic ...` 是否正确

## 11. 安全建议

- 不要把带真实密码的 `config/sources.yml` 公开上传
- 不要把真实的 `AUTH_PASSWORD` 与 `AUTH_SESSION_SECRET` 公开上传
- 如果要对公网开放，至少放在反向代理后并增加访问控制
- 优先使用只读数据库账号
- 定期清理 `runtime/` 日志

## 12. 发布版与本地环境的隔离

本仓库支持“本地使用”和“对外发布”分离。

- 本地运行使用你自己的 `.env` 和 `config/sources.yml`
- 发布包通过脚本单独生成，不会自动带上你的本地配置

生成发布包：

```bash
make release-bundle
make verify-release
```

生成后会得到：

- `dist/new-api-log-statistics-0.2.0/`
- `dist/new-api-log-statistics-0.2.0.tar.gz`

发布包默认不包含这些内容：

- 你的 `.env`
- 你的 `config/sources.yml`
- 运行日志
- 阶段性任务文档
- 本地验证脚本和样例导出文件

## 12.1 发布后冒烟验证

服务启动后，可以先跑基础冒烟：

```bash
make smoke
```

如果你想连带检查某个真实数据源和令牌：

```bash
SOURCE_ID=prod-main TOKEN_NAME=team-prod-token make smoke
```

## 13. 已知限制

- 当前默认没有登录鉴权，建议部署在受控网络内
- 当前已经支持可选登录鉴权，但默认仍是关闭状态
- 预聚合表需要你明确执行相关脚本后才会落库
- 当前没有完整的浏览器自动化测试，发布前建议手工回归一次关键查询链路
