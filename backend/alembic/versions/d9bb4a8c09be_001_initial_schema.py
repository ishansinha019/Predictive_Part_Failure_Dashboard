"""001_initial_schema

Baseline schema for a new database. For a legacy database whose tables were
created outside Alembic, existing tables are kept and `prediction_logs` is
brought up to the baseline (NOT NULL columns, indexes, foreign keys).

Revision ID: d9bb4a8c09be
Revises:
Create Date: 2026-11-23 00:19:27.244061

"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9bb4a8c09be'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PREDICTION_LOG_NOT_NULL = (
    "machine_id", "part_id", "time_in_service_days",
    "prediction_score", "recommendation", "prediction_timestamp",
)
PREDICTION_LOG_INDEXES = {
    "ix_prediction_logs_id": ["id"],
    "ix_prediction_logs_machine_id": ["machine_id"],
    "ix_prediction_logs_part_id": ["part_id"],
    "ix_prediction_logs_prediction_timestamp": ["prediction_timestamp"],
    "ix_pred_machine_time": ["machine_id", "prediction_timestamp"],
    "ix_pred_part_score": ["part_id", "prediction_score"],
}
PREDICTION_LOG_FKS = {
    "machine_id": ("fk_prediction_logs_machine_id_machines", "machines"),
    "part_id": ("fk_prediction_logs_part_id_parts", "parts"),
}


def _create_users() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def _create_machines() -> None:
    op.create_table(
        "machines",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("machine_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("install_date", sa.DateTime(), nullable=True),
        sa.Column("last_maintenance_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_machines"),
    )
    op.create_index("ix_machines_id", "machines", ["id"], unique=False)


def _create_parts() -> None:
    op.create_table(
        "parts",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("expected_lifespan_days", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Float(), nullable=False),
        sa.Column("planned_repair_hours", sa.Float(), nullable=False),
        sa.Column("unplanned_repair_hours", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_parts"),
    )
    op.create_index("ix_parts_id", "parts", ["id"], unique=False)


def _create_prediction_logs() -> None:
    op.create_table(
        "prediction_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("machine_id", sa.String(length=50), nullable=False),
        sa.Column("part_id", sa.String(length=50), nullable=False),
        sa.Column("time_in_service_days", sa.Integer(), nullable=False),
        sa.Column("prediction_score", sa.Float(), nullable=False),
        sa.Column("recommendation", sa.String(length=255), nullable=False),
        sa.Column("prediction_timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"],
            name="fk_prediction_logs_machine_id_machines", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["part_id"], ["parts.id"],
            name="fk_prediction_logs_part_id_parts", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_prediction_logs"),
    )
    for name, columns in PREDICTION_LOG_INDEXES.items():
        op.create_index(name, "prediction_logs", columns, unique=False)


def _create_work_orders() -> None:
    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("machine_id", sa.String(length=50), nullable=False),
        sa.Column("part_id", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("scheduled_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["machine_id"], ["machines.id"],
            name="fk_work_orders_machine_id_machines", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["part_id"], ["parts.id"],
            name="fk_work_orders_part_id_parts", ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_work_orders"),
    )
    op.create_index("ix_work_orders_id", "work_orders", ["id"], unique=False)
    op.create_index("ix_work_orders_machine_id", "work_orders", ["machine_id"], unique=False)
    op.create_index("ix_work_orders_part_id", "work_orders", ["part_id"], unique=False)


def _orphan_count(bind, column: str, parent: str) -> int:
    return bind.execute(sa.text(
        f"SELECT COUNT(*) FROM prediction_logs c "
        f"LEFT JOIN {parent} p ON c.{column} = p.id "
        f"WHERE c.{column} IS NOT NULL AND p.id IS NULL"
    )).scalar_one()


def _repair_requested() -> bool:
    options = context.get_x_argument(as_dictionary=True)
    return options.get("repair_orphans", "").lower() in ("1", "true", "yes")


def _create_missing_machines(bind) -> None:
    """Registers machines referenced only by legacy prediction logs (type taken from the ID prefix)."""
    missing = bind.execute(sa.text(
        "SELECT DISTINCT c.machine_id FROM prediction_logs c "
        "LEFT JOIN machines m ON c.machine_id = m.id "
        "WHERE c.machine_id IS NOT NULL AND m.id IS NULL"
    )).scalars().all()
    machines = sa.table(
        "machines",
        sa.column("id"), sa.column("machine_type"), sa.column("status"),
    )
    op.bulk_insert(machines, [
        {"id": machine_id, "machine_type": (machine_id.split("-")[0] or "U")[:20], "status": "Operational"}
        for machine_id in missing
    ])


def _repair_legacy_prediction_logs(bind) -> None:
    inspector = sa.inspect(bind)
    columns = {c["name"]: c for c in inspector.get_columns("prediction_logs")}
    indexes = {i["name"] for i in inspector.get_indexes("prediction_logs")}
    existing_fks = {
        (tuple(fk["constrained_columns"]), fk["referred_table"])
        for fk in inspector.get_foreign_keys("prediction_logs")
    }

    nullable = [name for name in PREDICTION_LOG_NOT_NULL if columns[name]["nullable"]]
    missing_indexes = {n: c for n, c in PREDICTION_LOG_INDEXES.items() if n not in indexes}
    missing_fks = {
        column: spec for column, spec in PREDICTION_LOG_FKS.items()
        if ((column,), spec[1]) not in existing_fks
    }

    for column, (_, parent) in missing_fks.items():
        orphans = _orphan_count(bind, column, parent)
        if not orphans:
            continue
        if column == "machine_id" and _repair_requested():
            _create_missing_machines(bind)
            continue
        hint = (
            " To keep the data, take a backup and re-run with `alembic -x repair_orphans=true upgrade head`,"
            " which registers the missing machines."
            if column == "machine_id" else " Add the missing parts or remove those rows (after a backup)."
        )
        raise RuntimeError(
            f"prediction_logs has {orphans} rows whose {column} does not exist in {parent}.{hint}"
        )

    if not (nullable or missing_indexes or missing_fks):
        return

    with op.batch_alter_table("prediction_logs") as batch_op:
        for name in nullable:
            batch_op.alter_column(name, existing_type=columns[name]["type"], nullable=False)
        for name, cols in missing_indexes.items():
            batch_op.create_index(name, cols, unique=False)
        for column, (fk_name, parent) in missing_fks.items():
            batch_op.create_foreign_key(fk_name, parent, [column], ["id"], ondelete="CASCADE")


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())

    # Parents first so child foreign keys resolve.
    for table, create in (
        ("users", _create_users),
        ("machines", _create_machines),
        ("parts", _create_parts),
        ("prediction_logs", _create_prediction_logs),
        ("work_orders", _create_work_orders),
    ):
        if table not in existing:
            create()

    if "prediction_logs" in existing:
        _repair_legacy_prediction_logs(bind)


def downgrade() -> None:
    """Downgrade schema. Drops every application table and its data."""
    for table in ("work_orders", "prediction_logs", "parts", "machines", "users"):
        op.drop_table(table)
