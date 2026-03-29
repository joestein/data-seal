"""Make audit_events table append-only with database trigger.

Revision ID: 002_audit_append_only
Revises: 001_initial
Create Date: 2026-03-28 00:00:00.000000

Adds a PostgreSQL trigger that prevents UPDATE and DELETE operations
on the audit_events table, enforcing append-only behavior at the
database level for compliance and legal integrity.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002_audit_append_only"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the trigger function that prevents modifications
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_audit_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_events table is append-only: % operations are not permitted', TG_OP;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger to block UPDATE operations
    op.execute("""
        CREATE TRIGGER no_audit_update
        BEFORE UPDATE ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_modification();
    """)

    # Create trigger to block DELETE operations
    op.execute("""
        CREATE TRIGGER no_audit_delete
        BEFORE DELETE ON audit_events
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_modification();
    """)

    # Alter the webhook_endpoints.secret column to accommodate encrypted values
    import sqlalchemy as sa
    op.alter_column("webhook_endpoints", "secret", type_=sa.String(500))


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS no_audit_delete ON audit_events;")
    op.execute("DROP TRIGGER IF EXISTS no_audit_update ON audit_events;")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_modification();")
