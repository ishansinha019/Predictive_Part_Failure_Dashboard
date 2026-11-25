"""002_work_order_lifecycle

Adds technician assignment, prediction linkage and creator tracking to work
orders, records the model version on prediction logs, and enforces at most one
active work order per machine and part.

Revision ID: a3f1c2d4e5b6
Revises: d9bb4a8c09be
Create Date: 2026-11-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f1c2d4e5b6'
down_revision: Union[str, Sequence[str], None] = 'd9bb4a8c09be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ACTIVE = sa.text("status IN ('Open', 'In_Progress')")


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    duplicates = bind.execute(sa.text(
        "SELECT machine_id, part_id FROM work_orders "
        "WHERE status IN ('Open', 'In_Progress') "
        "GROUP BY machine_id, part_id HAVING COUNT(*) > 1"
    )).fetchall()
    if duplicates:
        raise RuntimeError(
            "Multiple active work orders exist for the same machine and part "
            f"({len(duplicates)} groups). Cancel or complete the duplicates before upgrading."
        )

    with op.batch_alter_table("prediction_logs") as batch_op:
        batch_op.add_column(sa.Column("model_version", sa.String(length=20), nullable=True))

    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.add_column(sa.Column("assigned_technician_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("prediction_log_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("created_by_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_work_orders_assigned_technician_id_users",
            "users", ["assigned_technician_id"], ["id"], ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_work_orders_prediction_log_id_prediction_logs",
            "prediction_logs", ["prediction_log_id"], ["id"], ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_work_orders_created_by_id_users",
            "users", ["created_by_id"], ["id"], ondelete="SET NULL",
        )
        batch_op.create_index("ix_work_orders_status", ["status"], unique=False)
        batch_op.create_index("ix_work_orders_assigned_technician_id", ["assigned_technician_id"], unique=False)
        batch_op.create_index("ix_work_orders_prediction_log_id", ["prediction_log_id"], unique=False)

    op.create_index(
        "uq_work_orders_active_machine_part",
        "work_orders",
        ["machine_id", "part_id"],
        unique=True,
        sqlite_where=ACTIVE,
        postgresql_where=ACTIVE,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_work_orders_active_machine_part", table_name="work_orders")

    with op.batch_alter_table("work_orders") as batch_op:
        batch_op.drop_index("ix_work_orders_prediction_log_id")
        batch_op.drop_index("ix_work_orders_assigned_technician_id")
        batch_op.drop_index("ix_work_orders_status")
        batch_op.drop_constraint("fk_work_orders_created_by_id_users", type_="foreignkey")
        batch_op.drop_constraint("fk_work_orders_prediction_log_id_prediction_logs", type_="foreignkey")
        batch_op.drop_constraint("fk_work_orders_assigned_technician_id_users", type_="foreignkey")
        batch_op.drop_column("created_by_id")
        batch_op.drop_column("prediction_log_id")
        batch_op.drop_column("assigned_technician_id")

    with op.batch_alter_table("prediction_logs") as batch_op:
        batch_op.drop_column("model_version")
