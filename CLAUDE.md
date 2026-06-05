# CS2 饰品量化监控平台

面向 CS2 饰品倒货决策的私有化监控平台。核心目标是持续采集饰品价格、在售数量、求购数量、成交量和跨平台价差，识别异常波动并推送告警，为买入、卖出、持有和观望提供数据参考。

## 技术栈

- **前端**: React + TypeScript + Vite / Next.js（二选一，按实际落地确定）+ Tailwind CSS
- **后端**: Python FastAPI + SQLAlchemy + PostgreSQL / TimescaleDB
- **任务与缓存**: Redis + APScheduler / Celery
- **数据分析**: pandas / numpy，用于波动率、分位数、异动检测和告警回测
- **推送**: Telegram Bot / 企业微信 Bot / 邮件，按部署环境选择

## 快速启动

```bash
# 1. 安装依赖（实际目录以项目落地为准）
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 2. 配置环境变量（在 backend/.env 中）
# DATABASE_URL=postgresql+asyncpg://...
# REDIS_URL=redis://localhost:6379/0
# MARKET_API_KEY=...
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...

# 3. 启动后端（监听所有网络接口，支持局域网访问）
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 启动采集/告警任务（命令按实际任务框架调整）
cd backend && python -m app.jobs.worker

# 5. 启动前端
cd frontend && npm run dev
# 本机访问: http://localhost:5173
# 局域网访问: http://<本机IP>:5173
```

## 项目结构

- `backend/` — Python FastAPI 后端
  - `app/models/` — 饰品、行情快照、成交记录、告警记录、策略配置等数据模型
  - `app/routers/` — 监控列表、单品详情、历史行情、告警、机会榜、策略配置 API
  - `app/services/` — 数据源接入、行情采集、异动检测、评分模型、推送服务
  - `app/jobs/` — 定时采集、告警生成、回测统计等后台任务
- `frontend/` — Web 监控盘
  - `src/components/` — 表格、图表、告警卡片、筛选器等 UI 组件
  - `src/pages/` 或 `src/routes/` — 监控总览、饰品详情、异动告警、机会榜、策略配置
  - `src/store/` — 自选池、筛选条件、实时告警等全局状态
  - `src/api/` — 后端 API 客户端层

## 开发规范

### Git 工作流

- 远程仓库: `git@github.com:SmallThreeStone/CS-Quantification.git`
- **新功能开发必须在 `feature/` 分支上进行**，禁止直接在 `master` 上改动
  - 分支命名: `feature/<功能简述>`，如 `feature/demo-mode`、`feature/share-card`
  - 开发完成后合并回 `master`
- **每次推送代码时**:
  1. 必须更新 `README.md` 的当前版本与版本历史（包括版本号、改动摘要、必要的功能列表说明）
  2. 将 feature 分支合并到 `master`
  3. 推送到远程仓库
- 版本号规则:
  - 主功能/产品体验阶段升级使用大版本或次版本：`V0.1`、`V0.2`、`V1.0`
  - 同一阶段内的修复、细节优化、热修复使用小版本：`V0.1.1`、`V0.2.1`
  - 不允许只有 commit 版本号变化而 README 版本历史不同步
- Commit 风格: `V<版本号> — <简短描述>`，如 `V0.1.1 — 修复异动告警去重`

### 编码规范

- **默认不写注释**，只在 WHY 不明显时加一行简短注释
- 不写多行 docstring，不写 "used by X" / "added for Y" 类注释
- 优先编辑现有文件，避免新建文件
- 不做过度抽象：3 行相似代码好过 1 个过早的 helper
- 不引入 feature flag 或向后兼容 shim，直接改
- 不加不可能触发的错误处理、fallback 或验证
- TypeScript 编译零错误才能提交

### 提交前置自测（强制执行）

**每次代码修改后必须本地自测通过才能 `git commit` + `git push`，跨会话强制执行。**

1. 确保 TypeScript / Python 编译零错误
2. 启动本地服务（backend + frontend + Redis / 数据库，按当前实现需要）
3. 至少验证：`/api/health` 200、监控列表接口 200、告警列表接口 200、前端首页可访问
4. 涉及数据采集或异动检测变更时，必须使用样例行情或测试数据验证：
   - 行情快照可正常入库
   - 在售数量、求购数量、底价、最高求购价变化能正确生成告警
   - 告警冷却、去重、等级计算符合策略配置
   - 推送内容包含时间、饰品、类型、变化详情、系统判断、历史告警简报
5. 涉及前端页面变更时，必须浏览器实测监控总览、饰品详情、异动告警、机会榜等受影响页面
6. 涉及数据库模型或迁移变更时，必须验证迁移可执行、回滚路径明确、已有数据不被误删
7. 无法自测时必须明确告知用户并给出最小测试步骤

### 云服务器部署规范

- **只能通过 git 拉取代码**：`cd /data/cs-market-monitor && git pull`，禁止 SFTP/SCP 上传单个文件
- **只能通过 Docker Compose 启动**，禁止在容器外运行任何项目进程
- **常规代码更新优先最小化重启，不默认重建镜像**：本地 commit + push → SSH 到服务器 → `git pull` 最新代码 → 仅重启受影响服务
- **不要为了普通后端代码修改执行 `docker compose down && docker compose up -d --build`**：后端 Python 代码、采集规则、告警规则、小范围运行时代码，优先用 `docker compose restart backend worker` 或对应服务名
- **必须重建镜像的情况**：`frontend/` 源码或静态构建产物变化、`package.json`/`package-lock.json`、`requirements.txt`、Dockerfile、docker-compose.yml、Node/Python 版本、系统依赖、构建脚本、镜像内路径结构发生变化时，执行 `docker compose up -d --build`
- **Docker 架构：多服务 Compose**。建议拆分为 frontend、backend、worker、postgres、redis，采集任务和 API 服务分离，便于单独重启和监控
- **容器内热更新前置检查**：先确认服务器 git 工作区干净、当前分支正确、目标 commit 与远端一致；pull 后必须确认实际 HEAD 等于本地已推送 commit
- **热更新后置检查**：重启后必须验证 `docker compose ps`、`/api/health`、公网首页 200、采集任务正常运行、告警推送服务无错误日志
- **仅配置/数据变更不必重建镜像**：只改 `.env`、策略配置、数据库、缓存、运行时数据时，用 `docker compose restart` 或 `docker compose up -d`
- **数据库部署必须保留数据卷**：PostgreSQL / TimescaleDB 数据卷不得随普通部署删除；执行任何可能影响数据卷的命令前必须明确确认
- **部署后必须观察一轮采集周期**：确认至少一个监控池完成采集，行情快照入库，异常情况下不会批量误推送
- **不按版本区分镜像**：每次 build 覆盖当前项目 `latest` 镜像即可，不搞版本 tag，避免镜像堆积

### 任务执行

- 多步骤任务使用 TaskCreate/TaskUpdate 追踪进度
- 独立工作并行执行（同时启动多个 agent 或 tool call）
- 每轮完成后简要汇报改动内容和下一步

## 当前版本

V0.1.28 — 增加参考信号

## 环境要求

- Python 3.11+（路径：`C:/Users/31397/AppData/Local/Programs/Python/Python311/python.exe`）
- Node.js 18+（路径：`E:/nodejs/node.exe`）
- PostgreSQL 15+ / TimescaleDB（生产环境建议启用）
- Redis 7+
- Docker + Docker Compose（云服务器部署必须使用）
- 至少一个可用的 CS2 市场数据源 API Key 或合规数据采集入口
- Telegram Bot Token / 企业微信 Bot Webhook / 邮件 SMTP（三选一，用于异动推送）
