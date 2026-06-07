# CS2 饰品量化监控平台

私有化 CS2 饰品监控盘，用于持续采集饰品行情、识别在售/求购/底价异动、生成告警，并为买入、卖出、持有、观望提供数据参考。

## 当前版本

V0.1.64 — 增加 Linux 部署验证脚本

## 功能范围

- 默认测试饰品：100 个初始监控饰品，超导体、清凉薄荷在重点池，其余武器、手套、刀、箱子和贴纸在观察池
- 监控范围摘要：展示启用饰品数、P1 范围状态、缺失 Steam NameID、监控池和品类分布
- 监控总览：底价、在售、最高求购、求购、24h 成交、买入分、卖出分，支持按核心列排序
- 饰品详情：价格、在售、求购、成交、买卖盘价差趋势、时间段热力图、历史告警简报、历史告警时间线与历史告警
- 品类策略：按饰品分类输出策略画像、买入/卖出分修正和解释理由
- 机会榜：按当前评分、品类策略和同类告警回测表现综合排序，展示回测胜率与排序修正
- 告警回测：展示统计汇总、最近结果和基于 60 分钟窗口的阈值调参建议
- 异动告警：在售变化、求购变化、底价变化、价格波动异常、成交量异常，支持按饰品、类型、严重度和平台筛选
- 告警覆盖：展示告警类型覆盖、近 24h 告警、可追溯快照比例和最近告警
- 推送记录：支持微信 / QQ Webhook 适配，推送消息包含在售/求购/底价/波动/成交分组历史简报，未配置时记录 skipped
- 推送熔断：本轮采集真实字段占比过低或 fallback 覆盖过高时跳过外部推送并保留 skipped 记录
- 机会榜：按买入机会、卖压风险、扫货拉升、异常波动和观察候选分组排序
- 参考信号：基于降权后买入/卖出分、告警方向和数据可信度输出买入、持有、卖出、观望
- 买卖盘价差：监控总览展示价差率和价差金额，饰品详情展示价差趋势
- 净价差：策略配置支持卖出手续费、提现费率和汇率/折算系数，监控和详情展示扣费后净价差
- 可信度降权：低可信饰品会降低买入/卖出参考分，机会榜按降权后分数排序
- 策略配置：在售变化、求购变化、底价变化、价格波动异常、成交量异常、冷却时间和可信度最大降权可调
- 饰品管理：新增、编辑、停用、恢复监控饰品
- 饰品 Steam NameID：在饰品管理中维护订单簿 `item_nameid`
- Steam NameID 待办：展示覆盖率、缺失数量、按监控池分布和前 20 个待补齐饰品
- Steam NameID 发现：可从饰品管理页触发自动发现并写回字段
- Steam 订单簿验证：可在饰品管理页校验 NameID 是否能获取真实在售/求购深度
- Steam NameID 批量维护：支持批量发现缺失 ID 和批量验证订单簿深度
- 监控池：重点池、观察池、事件池分组，支持新增、编辑池名称、采集间隔和说明，worker 按池间隔采集
- worker 调度：支持通过 `WORKER_SLEEP_SECONDS` 配置后台轮询间隔
- 运行时体检：数据源状态页和部署验证脚本展示版本、数据库类型、推送配置、worker 间隔和 CORS 数量
- 部署环境审计：检查数据库类型、默认密码、行情源、订单簿、推送、worker 间隔和 CORS 配置风险
- 上线验收摘要：按 15 条上线前验收标准汇总通过、待复盘和阻断项，并展示证据
- MVP 范围摘要：汇总监控总览、饰品详情、异动告警、机会榜、推送模块和历史告警简报的具备状态
- 告警回测：记录告警后多窗口价格变化、胜率和平均变化
- 采集日志：记录每轮采集的状态、耗时、快照数、告警数和错误数
- 数据源状态：展示 Mock / Steam 适配层、订单簿开关、真实字段占比、补位字段、fallback 次数、最近错误和运维健康指标
- 数据源配置：展示当前 provider、订单簿开关、Steam NameID 覆盖率和配置建议
- 字段真实率：按底价、在售、最高求购、求购、成交和均价统计真实字段占比，辅助验证数据源准确性
- 运维健康：在数据源状态页展示采集成功率、推送成功率、worker 延迟、快照/告警数量和数据源异常计数
- API 响应时间：展示近 15 分钟请求数、平均耗时、P95、慢请求和 5xx 错误数量
- 数据库写入量：展示近 24 小时行情快照、告警、推送、回测和采集日志写入量、总行数和最新写入时间
- 主机资源巡检：展示 CPU、内存和磁盘占用，辅助云服务器部署后判断资源压力
- 备份状态巡检：展示数据库备份和配置备份脚本、最近文件、大小、时间和过期状态，支持 Linux `.sh` 与 Windows PowerShell 脚本
- 部署验证：支持 Linux `verify_deploy.sh` 和 Windows PowerShell `verify_deploy.ps1` 巡检核心 API、前端首页和可选采集
- P0 就绪度：展示观察天数、采集轮次、快照覆盖率和 7 天复盘状态
- P0 验证摘要：聚合数据源配置、连续采集、字段真实率、告警数量、阻塞项和复盘检查项
- 数据保留：数据源状态页展示行情快照、告警、回测和采集日志的保留策略、当前数据量和最早记录时间，支持清理过期快照与采集日志
- 饰品数据可信度：监控列表展示真实字段占比，数据源页列出低可信饰品
- 数据库迁移：Alembic 基线迁移，后端容器启动前自动执行迁移
- Docker Compose：frontend、backend、worker、postgres、redis，backend / worker 透传 Steam 订单簿配置，backend 只读挂载 `scripts/` 与 `backups/` 用于巡检备份状态

## 环境变量

复制 `.env.example` 为 `.env`，至少修改：

```bash
POSTGRES_PASSWORD=change_me
MARKET_PROVIDER=mock
STEAM_ORDERBOOK_ENABLED=false
WORKER_SLEEP_SECONDS=60
PUSH_CHANNEL=none
```

Steam 订单簿深度优先读取饰品管理里的 `Steam NameID`；也可用环境变量做兜底映射，例如：

```bash
MARKET_PROVIDER=steam
STEAM_ORDERBOOK_ENABLED=true
STEAM_ORDERBOOK_ITEM_NAMEIDS={"AK-47 | Test":"12345"}
```

## 本地启动

### 后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`

### 手动采集一轮

```bash
curl -X POST http://localhost:8000/api/collect
```

### 数据库迁移

```bash
cd backend
alembic upgrade head
```

Docker 部署时后端容器会自动执行迁移；`requirements.txt`、`Dockerfile` 或迁移文件变化后需要重建后端镜像。

## Docker Compose

```bash
docker compose up -d --build
```

访问：`http://localhost`

### 部署验证

```powershell
.\scripts\verify_deploy.ps1 -BaseUrl http://localhost
.\scripts\verify_deploy.ps1 -BaseUrl http://localhost -Collect
```

OpenCloud OS 9 / Linux 云服务器优先使用：

```bash
bash scripts/verify_deploy.sh --base-url http://localhost
bash scripts/verify_deploy.sh --base-url http://localhost --collect
```

验证脚本需要服务器已安装 Docker Compose，并且项目服务已经启动。

### 数据库备份

```powershell
.\scripts\backup_postgres.ps1
.\scripts\backup_postgres.ps1 -BackupDir ./backups/postgres -RetentionDays 14
```

OpenCloud OS 9 / Linux 云服务器优先使用：

```bash
bash scripts/backup_postgres.sh
bash scripts/backup_postgres.sh --backup-dir ./backups/postgres --retention-days 14
```

备份脚本通过 Docker Compose 调用 `postgres` 服务内的 `pg_dump`，生成带时间戳的 `.dump` 文件，并按保留天数清理旧备份。

### 配置备份

```powershell
.\scripts\backup_config.ps1
.\scripts\backup_config.ps1 -BackupDir ./backups/config -RetentionDays 30
```

OpenCloud OS 9 / Linux 云服务器优先使用：

```bash
bash scripts/backup_config.sh
bash scripts/backup_config.sh --backup-dir ./backups/config --retention-days 30
```

配置备份会打包 `.env`、`.env.example`、`docker-compose.yml`、`README.md`、`CLAUDE.md` 和 `scripts/`，生成带时间戳的 `.zip` 文件。

## API

- `GET /api/health`
- `GET /api/ops/health`
- `GET /api/ops/api-latency`
- `GET /api/ops/db-write-volume`
- `GET /api/ops/host-resources`
- `GET /api/ops/backups`
- `GET /api/ops/readiness`
- `GET /api/ops/runtime`
- `GET /api/ops/runtime-audit`
- `GET /api/ops/acceptance`
- `GET /api/ops/mvp-scope`
- `GET /api/ops/p0-summary`
- `GET /api/source/config`
- `GET /api/source/field-quality`
- `GET /api/retention`
- `POST /api/retention/cleanup`
- `POST /api/collect`
- `GET /api/monitor`
- `GET /api/monitor/coverage`
- `GET /api/items`
- `POST /api/items`
- `GET /api/items/{item_id}`
- `GET /api/items/{item_id}/history/price`
- `GET /api/items/{item_id}/history/sell`
- `GET /api/items/{item_id}/history/buy`
- `PUT /api/items/{item_id}`
- `PATCH /api/items/{item_id}/active`
- `GET /api/steam-nameids/todo`
- `GET /api/alerts/coverage`
- `GET /api/monitor-pools`
- `POST /api/monitor-pools`
- `PUT /api/monitor-pools/{pool_id}`
- `GET /api/collect-runs`
- `GET /api/alerts`
- `GET /api/backtests`
- `GET /api/backtests/summary`
- `GET /api/backtests/tuning-suggestions`
- `POST /api/backtests/evaluate`
- `GET /api/push-records`
- `GET /api/strategy`
- `PUT /api/strategy`
- `GET /api/opportunities`

## 推送配置

```bash
# 企业微信机器人
PUSH_CHANNEL=wechat
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...

# QQ 机器人网关
PUSH_CHANNEL=qq
QQ_WEBHOOK_URL=https://...
```

未配置 Webhook 时，系统只记录推送状态为 `skipped`，不会阻断行情采集和告警入库。

## 版本历史

- V0.1.64 — 增加 Linux 部署验证脚本，支持 OpenCloud OS 9 通过 bash 巡检核心 API、前端首页和可选采集。
- V0.1.63 — 增加 Linux 备份脚本，支持 OpenCloud OS 9 通过 bash 执行数据库和配置备份。
- V0.1.62 — 增加备份状态巡检，展示数据库/配置备份脚本、最近备份文件、大小、时间和过期状态。
- V0.1.61 — 增加主机资源巡检，展示 CPU、内存、磁盘占用并纳入部署验证脚本。
- V0.1.60 — 增加数据库写入量监控，展示近 24 小时写入量、总行数和最新写入时间。
- V0.1.59 — 增加 API 响应时间监控，展示近 15 分钟请求数、平均耗时、P95、慢请求和 5xx 错误数量。
- V0.1.58 — 增加 MVP 范围摘要，汇总 P1 页面与模块具备状态并纳入部署验证脚本。
- V0.1.57 — 增加 Steam NameID 待办摘要，展示覆盖率、缺失数量、监控池分布和前 20 个待补齐饰品。
- V0.1.56 — 增加监控范围摘要，展示 P1 范围状态、缺失 Steam NameID、监控池和品类分布。
- V0.1.55 — 扩充默认监控饰品到 100 个，覆盖常见武器、手套、刀、箱子、贴纸和胶囊。
- V0.1.54 — 增加上线验收摘要，按 15 条上线前验收标准汇总通过、待复盘和阻断项。
- V0.1.53 — 增加部署环境审计，检查数据库类型、默认密码、行情源、订单簿、推送、worker 间隔和 CORS 配置风险。
- V0.1.52 — 增加运行时配置体检，展示版本、数据库类型、数据源、推送配置、worker 间隔和 CORS 数量。
- V0.1.51 — 增加 worker 调度间隔配置，支持通过 `WORKER_SLEEP_SECONDS` 调整后台轮询频率。
- V0.1.50 — 补齐 Docker Compose 中 backend 和 worker 的 Steam 订单簿环境变量透传。
- V0.1.49 — 增加告警覆盖摘要，展示告警类型覆盖、近 24h 告警、可追溯快照比例和最近告警。
- V0.1.48 — 增加 P0 验证摘要，聚合数据源配置、连续采集、字段真实率、告警数量、阻塞项和复盘检查项。
- V0.1.47 — 增加数据源配置检查，展示 provider、订单簿开关、Steam NameID 覆盖率和配置建议。
- V0.1.46 — 增加字段真实率统计，按底价、在售、最高求购、求购、成交和均价展示真实/补位占比。
- V0.1.45 — 增加 P0 采集就绪度，汇总观察天数、采集轮次、快照覆盖率和 7 天复盘状态，并纳入部署验证脚本。
- V0.1.44 — 扩充默认测试饰品清单，初始化 30 个 P0 验证饰品并按重点池、观察池分组。
- V0.1.43 — 增加数据保留清理接口，按策略清理过期行情快照和采集日志，并保留被告警引用的快照。
- V0.1.42 — 数据源页展示数据保留策略，可查看行情快照、告警、回测和采集日志的保留周期、数量和最早时间。
- V0.1.41 — 增加数据保留策略接口，展示行情快照、告警、回测和采集日志的保留周期、数量和最早时间。
- V0.1.40 — 增加配置备份脚本，打包环境变量、Compose、项目说明和部署脚本并按保留天数清理。
- V0.1.39 — 数据源状态页展示运维健康指标，包括采集/推送成功率、worker 延迟、24h 快照、告警和异常数。
- V0.1.38 — 增加运维健康接口，汇总采集、推送、worker 延迟、快照、告警和数据源异常指标。
- V0.1.37 — 增加数据源异常推送熔断，本轮采集质量过低时跳过外部推送并记录原因。
- V0.1.36 — 增加 PostgreSQL 备份脚本，支持 Docker Compose 环境生成 `.dump` 备份并按保留天数清理。
- V0.1.35 — 增加回测调参建议，根据同类告警 60 分钟样本给出继续观察、收紧阈值、适度放宽或保持当前。
- V0.1.34 — 机会榜接入同类告警 60 分钟回测信号，展示样本数、胜率、平均变化和排序修正。
- V0.1.33 — 增加品类策略画像，按手套、武器、箱子/贴纸等分类修正买入/卖出参考分并展示理由。
- V0.1.32 — 增加回测最大上涨、最大回撤、盈亏比和样本置信等级，回测页展示评估时间。
- V0.1.31 — 增加卖出手续费、提现费率和汇率配置，快照输出净卖价、净价差和净价差率。
- V0.1.30 — 增加饰品详情历史告警时间线，按时间展示告警类型、方向、变化值和变化率。
- V0.1.29 — 增加快照买卖盘价差金额与价差率，监控总览支持价差率排序，饰品详情展示价差趋势图。
- V0.1.28 — 增加买入、持有、卖出、观望参考信号，监控总览、饰品详情和机会卡片展示信号与依据。
- V0.1.27 — 增加监控池新增和编辑 API，饰品管理页支持维护池名称、采集间隔和说明。
- V0.1.26 — 增加价格历史、在售历史和求购历史 API，支持独立拉取单品指标序列。
- V0.1.25 — 增强机会榜分组视图，按买入机会、卖压风险、扫货拉升、异常波动和观察候选聚合。
- V0.1.24 — 增加监控总览表头排序，支持按状态、底价、在售、求购、成交量和评分排序。
- V0.1.23 — 增加告警 API 查询参数和前端告警筛选控件。
- V0.1.22 — 增加价格波动异常告警和策略阈值，推送历史简报新增波动分组。
- V0.1.21 — 增加成交量异常告警和策略阈值，推送历史简报新增成交分组。
- V0.1.20 — 增强异动推送历史简报，按在售、求购、底价分组展示近 3 次历史告警。
- V0.1.19 — 增加可信度最大降权策略配置，监控、详情和机会榜按配置计算调整后分数。
- V0.1.18 — 增加数据可信度对买入/卖出参考分的降权，机会榜按调整后分数排序。
- V0.1.17 — 增加单饰品最新快照数据可信度摘要，监控列表展示可信度标签，数据源页列出低可信饰品。
- V0.1.16 — 增加 Steam NameID 批量发现、批量验证接口和前端批量操作按钮。
- V0.1.15 — 增加 Steam 订单簿验证接口和前端验深度按钮，发现 NameID 后可立即校验深度数据。
- V0.1.14 — 增加 Steam NameID 自动发现服务、写回接口和前端发现按钮。
- V0.1.13 — 增加饰品级 Steam NameID 字段、管理表单和迁移，订单簿优先读取饰品配置。
- V0.1.12 — 增加可选 Steam 订单簿适配，配置 item_nameid 后可用真实在售/求购深度替代补位字段。
- V0.1.11 — 增加采集数据源质量指标，展示真实字段、补位字段、fallback 次数和最近错误。
- V0.1.10 — 增加单品详情时间段热力图和按类型聚合的历史告警简报。
- V0.1.9 — 增加 Alembic 迁移基线、迁移启动器和迁移自测，后端容器启动前自动升级数据库。
- V0.1.8 — 增强 Docker Compose 健康检查、重启策略、环境变量模板和部署验证脚本。
- V0.1.7 — 增加采集运行日志、采集状态 API 和数据源状态页采集记录展示。
- V0.1.6 — 增加告警回测结果表、回测服务、回测 API 和前端回测页。
- V0.1.5 — 增加监控池分组、饰品池归属、池状态接口和 worker 到期池采集。
- V0.1.4 — 增加饰品管理 API 和前端管理页，支持新增、编辑、停用、恢复监控饰品。
- V0.1.3 — 增加策略配置读取/更新 API，前端策略页支持编辑告警阈值和冷却时间。
- V0.1.2 — 增加微信 / QQ Webhook 推送适配、推送记录表和站内推送状态展示。
- V0.1.1 — 忽略本地开发日志。
- V0.1 — 初始化 FastAPI 后端、Vite 前端、行情快照、异动告警、机会榜、Docker Compose 和 README。
