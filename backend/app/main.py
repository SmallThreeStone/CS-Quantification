from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers.market import router
from app.schema_bootstrap import ensure_runtime_columns
from app.services.api_metrics import api_metrics_store
from app.services.seed import seed_defaults


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)
    ensure_runtime_columns(engine)
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()
    app = FastAPI(title="CS2 饰品量化监控平台", version="0.1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def api_latency_middleware(request: Request, call_next) -> Response:
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            if request.url.path.startswith("/api"):
                duration_ms = (perf_counter() - started) * 1000
                api_metrics_store.record(request.url.path, request.method, status_code, duration_ms)

    app.include_router(router, prefix="/api")
    return app


app = create_app()
