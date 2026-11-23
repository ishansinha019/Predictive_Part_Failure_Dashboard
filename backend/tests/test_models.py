import pytest
from datetime import datetime
from app.models.user import User
from app.models.machine import Machine
from app.models.part import Part
from app.models.prediction_log import PredictionLog
from app.models.work_order import WorkOrder

def test_create_and_query_machine_with_logs(db_session):
    # 1. Create a machine
    machine = Machine(
        id="M-TEST-01",
        machine_type="M",
        status="Operational",
        install_date=datetime.utcnow(),
    )
    db_session.add(machine)

    # 2. Create a part
    part = Part(
        id="P-TEST-BRG",
        category="Bearing",
        name="Test High-Load Bearing",
        expected_lifespan_days=400,
        unit_cost=5000.0,
    )
    db_session.add(part)
    db_session.commit()

    # 3. Create a prediction log linked to machine and part
    log = PredictionLog(
        machine_id="M-TEST-01",
        part_id="P-TEST-BRG",
        time_in_service_days=250,
        prediction_score=0.15,
        recommendation="Routine Check",
        prediction_timestamp=datetime.utcnow(),
    )
    db_session.add(log)
    db_session.commit()

    # Query back and verify relationships
    saved_machine = db_session.query(Machine).filter(Machine.id == "M-TEST-01").first()
    assert saved_machine is not None
    assert len(saved_machine.prediction_logs) == 1
    assert saved_machine.prediction_logs[0].part_id == "P-TEST-BRG"
    assert saved_machine.prediction_logs[0].prediction_score == 0.15

def test_work_order_creation_and_status(db_session):
    machine = Machine(id="H-TEST-99", machine_type="H", status="Maintenance")
    part = Part(id="P-TEST-VLV", category="Valve", name="Test Valve", unit_cost=750.0)
    db_session.add_all([machine, part])
    db_session.commit()

    wo = WorkOrder(
        machine_id="H-TEST-99",
        part_id="P-TEST-VLV",
        status="Open",
        priority="Critical",
        estimated_cost=2500.0,
        notes="Automated alert from prediction model.",
    )
    db_session.add(wo)
    db_session.commit()

    saved_wo = db_session.query(WorkOrder).filter(WorkOrder.machine_id == "H-TEST-99").first()
    assert saved_wo is not None
    assert saved_wo.status == "Open"
    assert saved_wo.priority == "Critical"
    assert saved_wo.estimated_cost == 2500.0
