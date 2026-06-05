from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers.market import router
from app.schema_bootstrap import ensure_runtime_columns
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
    app.include_router(router, prefix="/api")
    return app


app = create_app()
