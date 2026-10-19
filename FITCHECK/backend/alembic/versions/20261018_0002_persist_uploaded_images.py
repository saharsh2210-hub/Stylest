"""Store uploaded images in the database for persistent hosted storage."""

from alembic import op
import sqlalchemy as sa

revision = "20261018_0002"
down_revision = "20261018_0001"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    existing_columns = {
        column["name"] for column in inspector.get_columns("wardrobe_items")
    }
    if "image_data" not in existing_columns:
        op.add_column(
            "wardrobe_items",
            sa.Column("image_data", sa.LargeBinary(), nullable=True),
        )
    if "image_content_type" not in existing_columns:
        op.add_column(
            "wardrobe_items",
            sa.Column("image_content_type", sa.String(length=40), nullable=True),
        )


def downgrade():
    op.drop_column("wardrobe_items", "image_content_type")
    op.drop_column("wardrobe_items", "image_data")
