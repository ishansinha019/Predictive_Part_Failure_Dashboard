from pathlib import Path
import argparse

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext

from app.db.database import Base, enable_sqlite_foreign_keys
import app.db.models  # noqa: F401  (registers all tables on Base.metadata)

BACKEND_DIR = Path(__file__).resolve().parents[1]

# Schema produced by the pre-Alembic create_all: prediction_logs had nullable
# columns and no foreign keys.
LEGACY_DDL = [
    """CREATE TABLE users (id INTEGER NOT NULL PRIMARY KEY, username VARCHAR(50) NOT NULL,
       hashed_password VARCHAR(255) NOT NULL, role VARCHAR(20) NOT NULL, created_at DATETIME NOT NULL)""",
    "CREATE UNIQUE INDEX ix_users_username ON users (username)",
    "CREATE INDEX ix_users_id ON users (id)",
    """CREATE TABLE machines (id VARCHAR(50) NOT NULL PRIMARY KEY, machine_type VARCHAR(20) NOT NULL,
       status VARCHAR(30) NOT NULL, install_date DATETIME, last_maintenance_date DATETIME)""",
    "CREATE INDEX ix_machines_id ON machines (id)",
    """CREATE TABLE parts (id VARCHAR(50) NOT NULL PRIMARY KEY, category VARCHAR(50) NOT NULL,
       name VARCHAR(100) NOT NULL, expected_lifespan_days INTEGER NOT NULL, unit_cost FLOAT NOT NULL,
       planned_repair_hours FLOAT NOT NULL, unplanned_repair_hours FLOAT NOT NULL)""",
    "CREATE INDEX ix_parts_id ON parts (id)",
    """CREATE TABLE prediction_logs (id INTEGER NOT NULL PRIMARY KEY, machine_id VARCHAR,
       part_id VARCHAR, time_in_service_days INTEGER, prediction_score FLOAT,
       recommendation VARCHAR, prediction_timestamp DATETIME)""",
    "CREATE INDEX ix_prediction_logs_id ON prediction_logs (id)",
    """CREATE TABLE work_orders (id INTEGER NOT NULL PRIMARY KEY, machine_id VARCHAR(50) NOT NULL,
       part_id VARCHAR(50) NOT NULL, status VARCHAR(30) NOT NULL, priority VARCHAR(20) NOT NULL,
       estimated_cost FLOAT NOT NULL, scheduled_date DATETIME, created_at DATETIME NOT NULL,
       completed_at DATETIME, notes TEXT,
       FOREIGN KEY(machine_id) REFERENCES machines (id) ON DELETE CASCADE,
       FOREIGN KEY(part_id) REFERENCES parts (id) ON DELETE CASCADE)""",
    "CREATE INDEX ix_work_orders_id ON work_orders (id)",
    "CREATE INDEX ix_work_orders_machine_id ON work_orders (machine_id)",
    "CREATE INDEX ix_work_orders_part_id ON work_orders (part_id)",
    "INSERT INTO machines (id, machine_type, status) VALUES ('M-1', 'M', 'Operational')",
    "INSERT INTO parts VALUES ('P-1', 'Bearing', 'Bearing', 500, 1000.0, 16.0, 56.0)",
    """INSERT INTO prediction_logs (machine_id, part_id, time_in_service_days, prediction_score,
       recommendation, prediction_timestamp) VALUES ('M-1', 'P-1', 100, 0.2, 'Historical Pass', '2024-01-01')""",
    """INSERT INTO work_orders (machine_id, part_id, status, priority, estimated_cost, created_at)
       VALUES ('M-1', 'P-1', 'Open', 'High', 10.0, '2024-01-02')""",
]


def alembic_config() -> Config:
    config = Config()
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return config


def run(engine, action, revision, x_args=()):
    config = alembic_config()
    config.cmd_opts = argparse.Namespace(x=list(x_args))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        action(config, revision)


@pytest.fixture
def engine(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    yield engine
    engine.dispose()


def schema_drift(engine):
    with engine.connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        return compare_metadata(context, Base.metadata)


def test_fresh_database_upgrades_to_model_schema(engine):
    run(engine, command.upgrade, "head")

    assert schema_drift(engine) == []


def test_migrations_downgrade_to_empty_database(engine):
    run(engine, command.upgrade, "head")
    run(engine, command.downgrade, "base")

    assert sa.inspect(engine).get_table_names() == ["alembic_version"]


def test_legacy_database_is_upgraded_without_losing_data(engine):
    with engine.begin() as connection:
        for statement in LEGACY_DDL:
            connection.execute(sa.text(statement))

    run(engine, command.upgrade, "head")

    assert schema_drift(engine) == []
    with engine.connect() as connection:
        assert connection.execute(sa.text("SELECT COUNT(*) FROM prediction_logs")).scalar_one() == 1
        assert connection.execute(sa.text("SELECT COUNT(*) FROM work_orders")).scalar_one() == 1
    inspector = sa.inspect(engine)
    referred = {fk["referred_table"] for fk in inspector.get_foreign_keys("prediction_logs")}
    assert referred == {"machines", "parts"}


def test_legacy_database_with_orphan_prediction_logs_is_not_upgraded(engine):
    with engine.begin() as connection:
        for statement in LEGACY_DDL:
            connection.execute(sa.text(statement))
        connection.execute(sa.text(
            """INSERT INTO prediction_logs (machine_id, part_id, time_in_service_days, prediction_score,
               recommendation, prediction_timestamp) VALUES ('UNKNOWN', 'P-1', 1, 0.1, 'x', '2024-01-01')"""
        ))

    with pytest.raises(Exception, match="does not exist in machines.*repair_orphans=true"):
        run(engine, command.upgrade, "head")


def test_orphan_machines_can_be_registered_when_repair_is_requested(engine):
    with engine.begin() as connection:
        for statement in LEGACY_DDL:
            connection.execute(sa.text(statement))
        connection.execute(sa.text(
            """INSERT INTO prediction_logs (machine_id, part_id, time_in_service_days, prediction_score,
               recommendation, prediction_timestamp) VALUES ('H-1003', 'P-1', 1, 0.1, 'x', '2024-01-01')"""
        ))

    run(engine, command.upgrade, "head", x_args=["repair_orphans=true"])

    with engine.connect() as connection:
        machine = connection.execute(sa.text("SELECT machine_type, status FROM machines WHERE id = 'H-1003'")).one()
        assert tuple(machine) == ("H", "Operational")
        assert connection.execute(sa.text("SELECT COUNT(*) FROM prediction_logs")).scalar_one() == 2
        assert connection.execute(sa.text("PRAGMA foreign_key_check")).fetchall() == []
    assert schema_drift(engine) == []


def test_foreign_keys_are_enforced_on_sqlite(engine):
    run(engine, command.upgrade, "head")
    strict_engine = sa.create_engine(str(engine.url))
    enable_sqlite_foreign_keys(strict_engine)

    with pytest.raises(sa.exc.IntegrityError):
        with strict_engine.begin() as connection:
            connection.execute(sa.text(
                """INSERT INTO prediction_logs (machine_id, part_id, time_in_service_days, prediction_score,
                   recommendation, prediction_timestamp) VALUES ('NOPE', 'NOPE', 1, 0.1, 'x', '2024-01-01')"""
            ))
    strict_engine.dispose()
