from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WardrobeItem(Base):
    __tablename__ = "wardrobe_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(80), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    image_data: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    image_content_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    primary_color: Mapped[str] = mapped_column(String(40), default="Unspecified", index=True)
    secondary_color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pattern: Mapped[str] = mapped_column(String(40), default="Solid")
    fit: Mapped[str] = mapped_column(String(40), default="Regular")
    material: Mapped[str | None] = mapped_column(String(80), nullable=True)
    style: Mapped[str | None] = mapped_column(String(80), nullable=True)
    suitable_occasions: Mapped[list[str]] = mapped_column(JSON, default=list)
    compatible_aesthetics: Mapped[list[str]] = mapped_column(JSON, default=list)
    seasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    laundry_status: Mapped[str] = mapped_column(String(20), default="clean", index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    last_worn: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    times_worn: Mapped[int] = mapped_column(Integer, default=0)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Outfit(Base):
    __tablename__ = "outfits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    item_ids: Mapped[list[str]] = mapped_column(JSON)
    aesthetic: Mapped[str] = mapped_column(String(60), default="Casual")
    occasion: Mapped[str] = mapped_column(String(60), default="Everyday")
    score: Mapped[float] = mapped_column(Float, default=0)
    explanation: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="generated", index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    planned_for: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    worn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
