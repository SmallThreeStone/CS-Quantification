import time

from app.database import SessionLocal
from app.main import create_app
from app.services.market_service import MarketService


def run_once() -> int:
    create_app()
    db = SessionLocal()
    try:
        alerts = MarketService(db).collect_active_items()
        return len(alerts)
    finally:
        db.close()


def main() -> None:
    while True:
        count = run_once()
        print(f"collected active items, alerts={count}", flush=True)
        time.sleep(600)


if __name__ == "__main__":
    main()
