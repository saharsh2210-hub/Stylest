from datetime import datetime

from pydantic import BaseModel, Field


class OutfitGenerate(BaseModel):
    aesthetic: str = Field(default="Casual", max_length=60)
    occasion: str = Field(default="Everyday", max_length=60)
    season: str | None = Field(default=None, max_length=20)
    exclude_item_ids: list[str] = Field(default_factory=list, max_length=100)
    seed: int | None = None


class OutfitAction(BaseModel):
    planned_for: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class OutfitRead(BaseModel):
    id: str
    item_ids: list[str]
    aesthetic: str
    occasion: str
    score: float
    explanation: list[str]
    status: str
    is_favorite: bool
    planned_for: str | None
    worn_at: datetime | None
    created_at: datetime
