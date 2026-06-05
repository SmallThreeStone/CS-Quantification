# CS2 饰品量化监控平台

私有化 CS2 饰品监控盘，用于持续采集饰品行情、识别在售/求购/底价异动、生成告警，并为买入、卖出、持有、观望提供数据参考。

## 当前版本

V0.1.22 — 增加价格波动异常告警

## 功能范围

- 重点池种子饰品：超导体、清凉薄荷
- 监控总览：底价、在售、最高求购、求购、24h 成交、买入分、卖出分
- 饰品详情：价格、在售、求购、成交趋势、时间段热力图、历史告警简报与历史告警
- 异动告警：在售变化、求购变化、底价变化、价格波动异常、成交量异常
- 推送记录：支持微信 / QQ Webhook 适配，推送消息包含在售/求购/底价/波动/成交分组历史简报，未配置时记录 skipped
- 机会榜：按买入分和卖出分排序
- 可信度降权：低可信饰品会降低买入/卖出参考分，机会榜按降权后分数排序
- 策略配置：在售变化、求购变化、底价变化、价格波动异常、成交量异常、冷却时间和可信度最大降权可调
- 饰品管理：新增、编辑、停用、恢复监控饰品
- 饰品 Steam NameID：在饰品管理中维护订单簿 `item_nameid`
- Steam NameID 发现：可从饰品管理页触发自动发现并写回字段
- Steam 订单簿验证：可在饰品管理页校验 NameID 是否能获取真实在售/求购深度
- Steam NameID 批量维护：支持批量发现缺失 ID 和批量验证订单簿深度
- 监控池：重点池、观察池、事件池分组，worker 按池间隔采集
- 告警回测：记录告警后多窗口价格变化、胜率和平均变化
- 采集日志：记录每轮采集的状态、耗时、快照数、告警数和错误数
- 数据源状态：展示 Mock / Steam 适配层、订单簿开关、真实字段占比、补位字段、fallback 次数和最近错误
- 饰品数据可信度：监控列表展示真实字段占比，数据源页列出低可信饰品
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
