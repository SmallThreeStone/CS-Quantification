import time

from app.config import settings
from app.database import SessionLocal
from app.main import create_app
from app.services.backtest_service import BacktestService
from app.services.market_service import MarketService
from app.services.push_service import PushService


def run_once() -> int:
    create_app()
    db = SessionLocal()
    try:
        market_service = MarketService(db)
        alerts = market_service.collect_due_pools()
        PushService(db).dispatch_alerts(alerts, market_service.push_suppress_reason())
        BacktestService(db).evaluate_due_alerts()
        return len(alerts)
    finally:
        db.close()


def main() -> None:
    sleep_seconds = max(1, settings.worker_sleep_seconds)
    while True:
        count = run_once()
        print(f"collected active items, alerts={count}", flush=True)
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
