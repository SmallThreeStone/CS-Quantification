from app.models import Item, MonitorPool, Platform, StrategyConfig
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.services.seed import seed_defaults
from tests.test_strategy_api import override_session


def test_seed_defaults_creates_one_hundred_test_items(db_session):
    seed_defaults(db_session)

    items = db_session.query(Item).all()
    pools = {pool.name: pool for pool in db_session.query(MonitorPool).all()}

    assert db_session.query(Platform).filter_by(code="steam").count() == 1
    assert db_session.query(StrategyConfig).filter_by(name="default").count() == 1
    assert len(items) == 100
    assert db_session.query(Item).filter(Item.is_active.is_(True)).count() == 100
    assert db_session.query(Item).filter_by(display_name="超导体", pool_id=pools["重点池"].id).count() == 1
    assert db_session.query(Item).filter_by(display_name="清凉薄荷", pool_id=pools["重点池"].id).count() == 1
    assert db_session.query(Item).filter(Item.pool_id == pools["观察池"].id).count() == 98


def test_monitor_coverage_reports_seed_distribution(db_session):
    seed_defaults(db_session)
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/monitor/coverage")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    pools = {pool["name"]: pool for pool in body["pools"]}
    categories = {category["name"]: category for category in body["categories"]}
    assert body["status"] == "ready"
    assert body["active_item_count"] == 100
    assert body["total_item_count"] == 100
    assert body["p1_min_item_count"] == 100
    assert body["p1_max_item_count"] == 300
    assert body["missing_nameid_count"] == 100
    assert pools["重点池"]["active_count"] == 2
    assert pools["观察池"]["active_count"] == 98
    assert categories["rifle"]["active_count"] >= 20


def test_monitor_coverage_marks_below_p1_scope(db_session):
    seed_defaults(db_session)
    db_session.query(Item).filter(Item.display_name != "超导体").update({"is_active": False}, synchronize_session=False)
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/monitor/coverage")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "below_p1"
    assert body["active_item_count"] == 1


def test_steam_nameid_todo_reports_missing_seed_items(db_session):
    seed_defaults(db_session)
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/steam-nameids/todo")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    pools = {pool["name"]: pool for pool in body["pools"]}
    assert body["status"] == "missing"
    assert body["active_item_count"] == 100
    assert body["missing_count"] == 100
    assert body["coverage_rate"] == 0
    assert body["discoverable_count"] == 100
    assert len(body["missing_items"]) == 20
    assert pools["观察池"]["active_count"] == 98
    assert pools["重点池"]["active_count"] == 2


def test_steam_nameid_todo_reports_partial_coverage(db_session):
    seed_defaults(db_session)
    item = db_session.query(Item).filter_by(display_name="超导体").one()
    item.steam_item_nameid = "123"
    db_session.commit()
    app.dependency_overrides[get_db] = override_session(db_session)
    client = TestClient(app)

    response = client.get("/api/steam-nameids/todo")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial"
    assert body["missing_count"] == 99
    assert body["coverage_rate"] == 0.01
