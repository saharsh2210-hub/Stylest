"""Create wardrobe and outfit tables."""

from alembic import op
import sqlalchemy as sa

from app.db.database import Base
revision = "20261018_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = {
        name
        for name in ("wardrobe_items", "outfits")
        if inspector.has_table(name)
    }
    if existing_tables:
        if existing_tables != {"wardrobe_items", "outfits"}:
            raise RuntimeError("FITCHECK found a partially initialized wardrobe schema.")
        for table in Base.metadata.sorted_tables:
            actual_columns = {
                column["name"] for column in inspector.get_columns(table.name)
            }
            expected_columns = {column.name for column in table.columns} - {
                "image_data",
                "image_content_type",
            }
            if not expected_columns <= actual_columns:
                raise RuntimeError(f"FITCHECK schema is missing columns from {table.name}.")
        return

    op.create_table(
        "wardrobe_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("subcategory", sa.String(length=80), nullable=True),
        sa.Column("image_path", sa.String(length=300), nullable=True),
        sa.Column("primary_color", sa.String(length=40), nullable=False, server_default="Unspecified"),
        sa.Column("secondary_color", sa.String(length=40), nullable=True),
        sa.Column("pattern", sa.String(length=40), nullable=False, server_default="Solid"),
        sa.Column("fit", sa.String(length=40), nullable=False, server_default="Regular"),
        sa.Column("material", sa.String(length=80), nullable=True),
        sa.Column("style", sa.String(length=80), nullable=True),
        sa.Column("suitable_occasions", sa.JSON(), nullable=False),
        sa.Column("compatible_aesthetics", sa.JSON(), nullable=False),
        sa.Column("seasons", sa.JSON(), nullable=False),
        sa.Column("laundry_status", sa.String(length=20), nullable=False, server_default="clean"),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_worn", sa.DateTime(timezone=True), nullable=True),
        sa.Column("times_worn", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_wardrobe_items_name", "wardrobe_items", ["name"])
    op.create_index("ix_wardrobe_items_category", "wardrobe_items", ["category"])
    op.create_index("ix_wardrobe_items_primary_color", "wardrobe_items", ["primary_color"])
    op.create_index("ix_wardrobe_items_laundry_status", "wardrobe_items", ["laundry_status"])

    op.create_table(
        "outfits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("item_ids", sa.JSON(), nullable=False),
        sa.Column("aesthetic", sa.String(length=60), nullable=False, server_default="Casual"),
        sa.Column("occasion", sa.String(length=60), nullable=False, server_default="Everyday"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="generated"),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("planned_for", sa.String(length=10), nullable=True),
        sa.Column("worn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_outfits_status", "outfits", ["status"])
    op.create_index("ix_outfits_planned_for", "outfits", ["planned_for"])


def downgrade():
    op.drop_index("ix_outfits_planned_for", table_name="outfits")
    op.drop_index("ix_outfits_status", table_name="outfits")
    op.drop_table("outfits")
    op.drop_index("ix_wardrobe_items_laundry_status", table_name="wardrobe_items")
    op.drop_index("ix_wardrobe_items_primary_color", table_name="wardrobe_items")
    op.drop_index("ix_wardrobe_items_category", table_name="wardrobe_items")
    op.drop_index("ix_wardrobe_items_name", table_name="wardrobe_items")
    op.drop_table("wardrobe_items")
