# CS2 饰品量化监控平台

私有化 CS2 饰品监控盘，用于持续采集饰品行情、识别在售/求购/底价异动、生成告警，并为买入、卖出、持有、观望提供数据参考。

## 当前版本

V0.1 — MVP 骨架初始化

## 功能范围

- 重点池种子饰品：超导体、清凉薄荷
- 监控总览：底价、在售、最高求购、求购、24h 成交、买入分、卖出分
- 饰品详情：价格、在售、求购、成交趋势与历史告警
- 异动告警：在售变化、求购变化、底价变化
- 机会榜：按买入分和卖出分排序
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
- `GET /api/opportunities`

## 版本历史

- V0.1 — 初始化 FastAPI 后端、Vite 前端、行情快照、异动告警、机会榜、Docker Compose 和 README。
