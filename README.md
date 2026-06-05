# CS2 饰品量化监控平台

私有化 CS2 饰品监控盘，用于持续采集饰品行情、识别在售/求购/底价异动、生成告警，并为买入、卖出、持有、观望提供数据参考。

## 当前版本

V0.1.3 — 策略配置 API 与前端可编辑阈值

## 功能范围

- 重点池种子饰品：超导体、清凉薄荷
- 监控总览：底价、在售、最高求购、求购、24h 成交、买入分、卖出分
- 饰品详情：价格、在售、求购、成交趋势与历史告警
- 异动告警：在售变化、求购变化、底价变化
- 推送记录：支持微信 / QQ Webhook 适配，未配置时记录 skipped
- 机会榜：按买入分和卖出分排序
- 策略配置：在售变化、求购变化、底价变化和冷却时间可调
- 数据源状态：当前使用 Mock / Steam 适配层占位
- Docker Compose：frontend、backend、worker、postgres、redis

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

## Docker Compose

```bash
docker compose up -d --build
```

访问：`http://localhost`

## API

- `GET /api/health`
- `POST /api/collect`
- `GET /api/monitor`
- `GET /api/items/{item_id}`
- `GET /api/alerts`
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

- V0.1.3 — 增加策略配置读取/更新 API，前端策略页支持编辑告警阈值和冷却时间。
- V0.1.2 — 增加微信 / QQ Webhook 推送适配、推送记录表和站内推送状态展示。
- V0.1.1 — 忽略本地开发日志。
- V0.1 — 初始化 FastAPI 后端、Vite 前端、行情快照、异动告警、机会榜、Docker Compose 和 README。
