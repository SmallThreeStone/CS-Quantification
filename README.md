# CS2 饰品量化监控平台

私有化 CS2 饰品监控盘，用于持续采集饰品行情、识别在售/求购/底价异动、生成告警，并为买入、卖出、持有、观望提供数据参考。

## 当前版本

V0.1.13 — 饰品级 Steam NameID 管理

## 功能范围

- 重点池种子饰品：超导体、清凉薄荷
- 监控总览：底价、在售、最高求购、求购、24h 成交、买入分、卖出分
- 饰品详情：价格、在售、求购、成交趋势、时间段热力图、历史告警简报与历史告警
- 异动告警：在售变化、求购变化、底价变化
- 推送记录：支持微信 / QQ Webhook 适配，未配置时记录 skipped
- 机会榜：按买入分和卖出分排序
- 策略配置：在售变化、求购变化、底价变化和冷却时间可调
- 饰品管理：新增、编辑、停用、恢复监控饰品
- 饰品 Steam NameID：在饰品管理中维护订单簿 `item_nameid`
- 监控池：重点池、观察池、事件池分组，worker 按池间隔采集
- 告警回测：记录告警后多窗口价格变化、胜率和平均变化
- 采集日志：记录每轮采集的状态、耗时、快照数、告警数和错误数
- 数据源状态：展示 Mock / Steam 适配层、订单簿开关、真实字段占比、补位字段、fallback 次数和最近错误
- 数据库迁移：Alembic 基线迁移，后端容器启动前自动执行迁移
- Docker Compose：frontend、backend、worker、postgres、redis

## 环境变量

复制 `.env.example` 为 `.env`，至少修改：

```bash
POSTGRES_PASSWORD=change_me
MARKET_PROVIDER=mock
STEAM_ORDERBOOK_ENABLED=false
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

该脚本需要服务器已安装 Docker Compose，并且项目服务已经启动。

## API

- `GET /api/health`
- `POST /api/collect`
- `GET /api/monitor`
- `GET /api/items`
- `POST /api/items`
- `GET /api/items/{item_id}`
- `PUT /api/items/{item_id}`
- `PATCH /api/items/{item_id}/active`
- `GET /api/monitor-pools`
- `GET /api/collect-runs`
- `GET /api/alerts`
- `GET /api/backtests`
- `GET /api/backtests/summary`
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
