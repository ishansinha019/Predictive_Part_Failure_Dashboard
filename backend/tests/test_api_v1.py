from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.machine import Machine
from app.models.part import Part
from app.models.prediction_log import PredictionLog
from app.models.user import User
from app.services import ml_loader

PREDICT = "/api/v1/predictions/predict"
WORK_ORDERS = "/api/v1/work-orders"


def headers_for(user):
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


def make_user(db, username, role):
    user = User(username=username, hashed_password=get_password_hash("secret-pass"), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def fleet(db_session):
    db_session.add_all([
        Machine(id="M-100", machine_type="M", status="Operational"),
        Machine(id="M-200", machine_type="M", status="Operational"),
        Machine(id="H-300", machine_type="H", status="Offline"),
        Part(id="P-BRG-02", category="Bearing", name="Roller Bearing", unit_cost=12000.0),
        Part(id="P-VLV-01", category="Valve", name="Hydraulic Valve", unit_cost=600.0),
    ])
    db_session.commit()


@pytest.fixture
def technician(test_user):
    return test_user


@pytest.fixture
def other_technician(db_session):
    return make_user(db_session, "other.tech", "technician")


@pytest.fixture
def viewer(db_session):
    return make_user(db_session, "viewer1", "viewer")


@pytest.fixture
def model_score(monkeypatch):
    """Replaces model inference with a controllable score or error."""
    state = {"score": 0.8, "error": None}

    def fake_prediction(request, model_version=None):
        if state["error"]:
            raise state["error"]
        return state["score"]

    monkeypatch.setattr(ml_loader, "make_prediction", fake_prediction)
    return state


def predict(client, headers, machine="M-100", part="P-BRG-02", days=450):
    return client.post(
        PREDICT,
        json={"machine_id": machine, "part_id": part, "time_in_service_days": days},
        headers=headers,
    )


# --- Role enforcement ---

def test_viewer_is_read_only(client, fleet, viewer, model_score):
    headers = headers_for(viewer)

    assert client.get("/api/v1/machines/", headers=headers).status_code == 200
    assert client.get(WORK_ORDERS, headers=headers).status_code == 200
    assert predict(client, headers).status_code == 403
    create = client.post(WORK_ORDERS, json={"machine_id": "M-100", "part_id": "P-BRG-02"}, headers=headers)
    assert create.status_code == 403
    assert client.patch(f"{WORK_ORDERS}/1", json={"status": "In_Progress"}, headers=headers).status_code == 403


def test_daily_scan_is_admin_only(client, fleet, technician, admin_user, model_score, db_session):
    db_session.add(PredictionLog(
        machine_id="M-100", part_id="P-BRG-02", time_in_service_days=10,
        prediction_score=0.1, recommendation="No action needed", model_version="v1.0",
    ))
    db_session.commit()
    path = "/api/v1/simulation/daily-scan"

    assert client.post(path, headers=headers_for(technician)).status_code == 403

    response = client.post(path, headers=headers_for(admin_user))
    assert response.status_code == 200
    assert response.json()["machines_scanned"] == 1
    newest = db_session.query(PredictionLog).order_by(PredictionLog.id.desc()).first()
    assert newest.time_in_service_days == 11
    assert newest.model_version == settings.MODEL_VERSION


# --- Fleet listing ---

def add_log(db, machine_id, score, when, days=100, part_id="P-BRG-02"):
    db.add(PredictionLog(
        machine_id=machine_id, part_id=part_id, time_in_service_days=days,
        prediction_score=score, recommendation="x", prediction_timestamp=when, model_version="v1.0",
    ))
    db.commit()


def test_fleet_contract_and_latest_prediction(client, fleet, auth_headers, db_session):
    now = datetime(2026, 1, 10)
    add_log(db_session, "M-100", 0.2, now - timedelta(days=2))
    add_log(db_session, "M-100", 0.9, now)

    response = client.get("/api/v1/machines/", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "3"
    by_id = {m["machine_id"]: m for m in response.json()}
    assert set(by_id) == {"M-100", "M-200", "H-300"}
    assert by_id["M-100"]["latest_risk_score"] == 0.9
    assert by_id["M-100"]["last_updated"].startswith("2026-01-10")
    assert by_id["M-200"]["last_updated"] is None


def test_fleet_pagination_search_filter_and_sort(client, fleet, auth_headers, db_session):
    add_log(db_session, "M-100", 0.3, datetime(2026, 1, 1))
    add_log(db_session, "M-200", 0.7, datetime(2026, 1, 2))

    page = client.get("/api/v1/machines/?limit=1&skip=1", headers=auth_headers)
    assert [m["machine_id"] for m in page.json()] == ["M-100"]
    assert page.headers["X-Total-Count"] == "3"

    search = client.get("/api/v1/machines/?search=m-", headers=auth_headers)
    assert sorted(m["machine_id"] for m in search.json()) == ["M-100", "M-200"]
    assert search.headers["X-Total-Count"] == "2"

    literal_percent = client.get("/api/v1/machines/?search=%25", headers=auth_headers)
    assert literal_percent.json() == []

    offline = client.get("/api/v1/machines/?status=Offline", headers=auth_headers)
    assert [m["machine_id"] for m in offline.json()] == ["H-300"]

    by_risk = client.get("/api/v1/machines/?sort_by=risk&order=desc", headers=auth_headers)
    assert [m["machine_id"] for m in by_risk.json()] == ["M-200", "M-100", "H-300"]
    ascending = client.get("/api/v1/machines/?sort_by=risk&order=asc", headers=auth_headers)
    assert [m["machine_id"] for m in ascending.json()] == ["M-100", "M-200", "H-300"]


@pytest.mark.parametrize("query", ["limit=0", "limit=501", "skip=-1", "status=Broken", "sort_by=cost"])
def test_fleet_rejects_invalid_parameters(client, auth_headers, query):
    assert client.get(f"/api/v1/machines/?{query}", headers=auth_headers).status_code == 422


# --- Prediction and history ---

def test_predict_logs_result_and_updates_history(client, fleet, auth_headers, model_score):
    model_score["score"] = 0.82

    response = predict(client, auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["failure_risk"] == 0.82
    assert body["recommendation"] == "Recommend immediate replacement"
    assert body["model_version"] == settings.MODEL_VERSION

    history = client.get("/api/v1/machines/M-100/history", headers=auth_headers).json()
    assert [entry["id"] for entry in history] == [body["prediction_id"]]
    assert history[0]["time_in_service_days"] == 450
    assert history[0]["prediction_score"] == 0.82


@pytest.mark.parametrize(
    ("score", "recommendation"),
    [(0.2, "No action needed"), (0.6, "Schedule maintenance soon"), (0.9, "Recommend immediate replacement")],
)
def test_recommendation_thresholds(client, fleet, auth_headers, model_score, score, recommendation):
    model_score["score"] = score

    assert predict(client, auth_headers).json()["recommendation"] == recommendation


def test_predict_rejects_unknown_machine_part_and_bad_input(client, fleet, auth_headers, model_score, db_session):
    assert predict(client, auth_headers, machine="NOPE").status_code == 404
    assert predict(client, auth_headers, part="NOPE").status_code == 404
    assert predict(client, auth_headers, days=-1).status_code == 422
    assert client.post(PREDICT, json={"machine_id": "M-100"}, headers=auth_headers).status_code == 422
    assert db_session.query(PredictionLog).count() == 0


def test_model_failure_returns_503_without_leaking_details(client, fleet, auth_headers, model_score, db_session):
    model_score["error"] = RuntimeError("secret model path C:/internal/model.joblib")

    response = predict(client, auth_headers)

    assert response.status_code == 503
    assert "secret" not in response.text
    assert db_session.query(PredictionLog).count() == 0


def test_predict_with_bundled_v1_model(client, fleet, auth_headers):
    response = predict(client, auth_headers)

    assert response.status_code == 200
    assert 0.0 <= response.json()["failure_risk"] <= 1.0


def test_history_is_newest_first_paginated_and_404_for_unknown_machine(client, fleet, auth_headers, db_session):
    for day in range(1, 4):
        add_log(db_session, "M-100", 0.1 * day, datetime(2026, 1, day), days=day)

    history = client.get("/api/v1/machines/M-100/history?limit=2", headers=auth_headers).json()
    assert [entry["time_in_service_days"] for entry in history] == [3, 2]

    assert client.get("/api/v1/machines/M-100/history?skip=2", headers=auth_headers).json()[0]["time_in_service_days"] == 1
    assert client.get("/api/v1/machines/NOPE/history", headers=auth_headers).status_code == 404


def test_part_stats(client, fleet, auth_headers, db_session):
    add_log(db_session, "M-100", 0.9, datetime(2026, 1, 1), days=500)
    add_log(db_session, "M-100", 0.1, datetime(2026, 1, 2), days=50)

    ok = client.get("/api/v1/parts/P-BRG-02/stats", headers=auth_headers)
    assert ok.json() == {"time_to_failure_days": [500]}
    assert client.get("/api/v1/parts/NOPE/stats", headers=auth_headers).status_code == 404


# --- Work order lifecycle ---

def create_work_order(client, headers, **payload):
    body = {"machine_id": "M-100", "part_id": "P-BRG-02", **payload}
    return client.post(WORK_ORDERS, json=body, headers=headers)


def test_predict_to_work_order_to_completion(client, fleet, technician, model_score, db_session):
    headers = headers_for(technician)
    model_score["score"] = 0.92
    prediction_id = predict(client, headers).json()["prediction_id"]

    created = create_work_order(client, headers, prediction_id=prediction_id, notes="Bearing noise")
    assert created.status_code == 201
    work_order = created.json()
    assert work_order["status"] == "Open"
    assert work_order["priority"] == "Critical"
    assert work_order["estimated_cost"] == 12000.0
    assert work_order["prediction_log_id"] == prediction_id
    assert work_order["machine"]["id"] == "M-100"
    assert work_order["part"]["name"] == "Roller Bearing"
    assert work_order["assigned_technician"] is None

    pending = client.get(WORK_ORDERS, headers=headers)
    assert [w["id"] for w in pending.json()] == [work_order["id"]]
    assert pending.headers["X-Total-Count"] == "1"

    # A second active order for the same machine and part is refused.
    assert create_work_order(client, headers).status_code == 409

    work_url = f"{WORK_ORDERS}/{work_order['id']}"
    started = client.patch(work_url, json={"status": "In_Progress"}, headers=headers)
    assert started.status_code == 200
    assert db_session.get(Machine, "M-100").status == "Maintenance"

    done = client.patch(work_url, json={"status": "Completed"}, headers=headers)
    assert done.status_code == 200
    assert done.json()["completed_at"] is not None
    db_session.expire_all()
    machine = db_session.get(Machine, "M-100")
    assert machine.status == "Operational"
    assert machine.last_maintenance_date is not None

    assert client.get(WORK_ORDERS, headers=headers).json() == []
    completed = client.get(f"{WORK_ORDERS}?status=Completed", headers=headers).json()
    assert [w["id"] for w in completed] == [work_order["id"]]
    assert [h["id"] for h in client.get("/api/v1/machines/M-100/history", headers=headers).json()] == [prediction_id]

    # Closed orders are final, and a new order can be raised afterwards.
    assert client.patch(work_url, json={"notes": "late edit"}, headers=headers).status_code == 409
    assert create_work_order(client, headers).status_code == 201


def test_status_transitions_are_enforced(client, fleet, technician):
    headers = headers_for(technician)
    work_url = f"{WORK_ORDERS}/{create_work_order(client, headers).json()['id']}"

    assert client.patch(work_url, json={"status": "Completed"}, headers=headers).status_code == 409
    assert client.patch(work_url, json={"status": "Cancelled"}, headers=headers).status_code == 200
    assert client.patch(work_url, json={"status": "In_Progress"}, headers=headers).status_code == 409


def test_machine_stays_in_maintenance_while_another_order_is_in_progress(client, fleet, technician, db_session):
    headers = headers_for(technician)
    first = create_work_order(client, headers, part_id="P-BRG-02").json()["id"]
    second = create_work_order(client, headers, part_id="P-VLV-01").json()["id"]
    for work_id in (first, second):
        client.patch(f"{WORK_ORDERS}/{work_id}", json={"status": "In_Progress"}, headers=headers)

    client.patch(f"{WORK_ORDERS}/{first}", json={"status": "Completed"}, headers=headers)
    db_session.expire_all()
    assert db_session.get(Machine, "M-100").status == "Maintenance"

    client.patch(f"{WORK_ORDERS}/{second}", json={"status": "Cancelled"}, headers=headers)
    db_session.expire_all()
    assert db_session.get(Machine, "M-100").status == "Operational"


@pytest.mark.parametrize(
    ("score", "expected_priority"), [(0.95, "Critical"), (0.8, "High"), (0.6, "Medium")]
)
def test_priority_is_derived_from_risk(client, fleet, technician, model_score, score, expected_priority):
    headers = headers_for(technician)
    model_score["score"] = score
    prediction_id = predict(client, headers).json()["prediction_id"]

    created = create_work_order(client, headers, prediction_id=prediction_id)

    assert created.json()["priority"] == expected_priority


def test_prediction_must_justify_the_work_order(client, fleet, technician, model_score, db_session):
    headers = headers_for(technician)

    model_score["score"] = 0.3
    low_risk = predict(client, headers).json()["prediction_id"]
    assert create_work_order(client, headers, prediction_id=low_risk).status_code == 422

    model_score["score"] = 0.9
    other_machine = predict(client, headers, machine="M-200").json()["prediction_id"]
    assert create_work_order(client, headers, prediction_id=other_machine).status_code == 422

    assert create_work_order(client, headers, prediction_id=9999).status_code == 404

    historical = PredictionLog(
        machine_id="M-100", part_id="P-BRG-02", time_in_service_days=700,
        prediction_score=1.0, recommendation="Historical Failure",
    )
    db_session.add(historical)
    db_session.commit()
    assert create_work_order(client, headers, prediction_id=historical.id).status_code == 422


def test_experimental_model_predictions_cannot_create_work_orders(
    client, fleet, technician, model_score, monkeypatch
):
    headers = headers_for(technician)
    monkeypatch.setattr(settings, "MODEL_VERSION", "v2.0")
    prediction_id = predict(client, headers).json()["prediction_id"]

    response = create_work_order(client, headers, prediction_id=prediction_id)

    assert response.status_code == 422
    assert "experimental" in response.json()["detail"]
    # A manually raised order, with no model involved, is still allowed.
    assert create_work_order(client, headers).status_code == 201


def test_work_order_validation(client, fleet, technician):
    headers = headers_for(technician)

    assert create_work_order(client, headers, machine_id="NOPE").status_code == 404
    assert create_work_order(client, headers, part_id="NOPE").status_code == 404
    assert create_work_order(client, headers, priority="Urgent").status_code == 422
    assert create_work_order(client, headers, estimated_cost=-5).status_code == 422
    work_url = f"{WORK_ORDERS}/{create_work_order(client, headers).json()['id']}"
    assert client.patch(work_url, json={}, headers=headers).status_code == 422
    assert client.patch(work_url, json={"status": None}, headers=headers).status_code == 422
    assert client.patch(f"{WORK_ORDERS}/9999", json={"notes": "x"}, headers=headers).status_code == 404
    assert client.get(f"{WORK_ORDERS}/9999", headers=headers).status_code == 404


def test_work_order_list_filters_and_metadata(client, fleet, technician, admin_user):
    admin_headers = headers_for(admin_user)
    low = create_work_order(client, admin_headers, part_id="P-VLV-01", priority="Low",
                            assigned_technician_id=technician.id).json()
    critical = create_work_order(client, admin_headers, machine_id="M-200", priority="Critical").json()

    everything = client.get(WORK_ORDERS, headers=admin_headers).json()
    assert [w["id"] for w in everything] == [critical["id"], low["id"]]
    assert everything[1]["assigned_technician"] == {"id": technician.id, "username": technician.username}

    assert [w["id"] for w in client.get(f"{WORK_ORDERS}?priority=Low", headers=admin_headers).json()] == [low["id"]]
    assert [w["id"] for w in client.get(f"{WORK_ORDERS}?machine_id=M-200", headers=admin_headers).json()] == [critical["id"]]
    assigned = client.get(f"{WORK_ORDERS}?assigned_technician_id={technician.id}", headers=admin_headers)
    assert [w["id"] for w in assigned.json()] == [low["id"]]
    assert client.get(f"{WORK_ORDERS}?limit=1&skip=1", headers=admin_headers).json()[0]["id"] == low["id"]
    assert client.get(f"{WORK_ORDERS}?status=Unknown", headers=admin_headers).status_code == 422


def test_assignment_rules(client, fleet, technician, other_technician, viewer, admin_user):
    tech_headers = headers_for(technician)
    admin_headers = headers_for(admin_user)
    work_id = create_work_order(client, tech_headers).json()["id"]
    work_url = f"{WORK_ORDERS}/{work_id}"

    # Technicians can take work themselves, but not hand it to others.
    assert client.patch(work_url, json={"assigned_technician_id": other_technician.id}, headers=tech_headers).status_code == 403
    mine = client.patch(work_url, json={"assigned_technician_id": technician.id}, headers=tech_headers)
    assert mine.json()["assigned_technician"]["username"] == technician.username

    # Another technician cannot change it; an admin can reassign or unassign it.
    assert client.patch(work_url, json={"notes": "x"}, headers=headers_for(other_technician)).status_code == 403
    reassigned = client.patch(work_url, json={"assigned_technician_id": other_technician.id}, headers=admin_headers)
    assert reassigned.json()["assigned_technician"]["id"] == other_technician.id
    unassigned = client.patch(work_url, json={"assigned_technician_id": None}, headers=admin_headers)
    assert unassigned.json()["assigned_technician"] is None

    # Only existing users with the technician role can be assigned.
    for bad_id in (viewer.id, admin_user.id, 9999):
        response = client.patch(work_url, json={"assigned_technician_id": bad_id}, headers=admin_headers)
        assert response.status_code == 422


def test_work_order_routes_require_authentication(client):
    assert client.get(WORK_ORDERS).status_code == 401
    assert client.post(WORK_ORDERS, json={"machine_id": "M-1", "part_id": "P-1"}).status_code == 401
    assert client.patch(f"{WORK_ORDERS}/1", json={"notes": "x"}).status_code == 401


# --- Database integrity ---

def test_database_rejects_orphaned_prediction_logs(db_session):
    db_session.add(PredictionLog(
        machine_id="GHOST", part_id="GHOST", time_in_service_days=1,
        prediction_score=0.1, recommendation="x",
    ))

    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
