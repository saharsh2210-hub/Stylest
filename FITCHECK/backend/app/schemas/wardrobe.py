from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemFields(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=40)
    subcategory: str | None = Field(default=None, max_length=80)
    primary_color: str = Field(default="Unspecified", max_length=40)
    secondary_color: str | None = Field(default=None, max_length=40)
    pattern: str = Field(default="Solid", max_length=40)
    fit: str = Field(default="Regular", max_length=40)
    material: str | None = Field(default=None, max_length=80)
    style: str | None = Field(default=None, max_length=80)
    suitable_occasions: list[str] = Field(default_factory=list, max_length=20)
    compatible_aesthetics: list[str] = Field(default_factory=list, max_length=20)
    seasons: list[str] = Field(default_factory=list, max_length=4)
    laundry_status: str = Field(default="clean", pattern="^(clean|dirty|in_laundry)$")
    is_available: bool = True
    is_favorite: bool = False


class ItemCreate(ItemFields):
    pass


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, min_length=1, max_length=40)
    subcategory: str | None = Field(default=None, max_length=80)
    primary_color: str | None = Field(default=None, max_length=40)
    secondary_color: str | None = Field(default=None, max_length=40)
    pattern: str | None = Field(default=None, max_length=40)
    fit: str | None = Field(default=None, max_length=40)
    material: str | None = Field(default=None, max_length=80)
    style: str | None = Field(default=None, max_length=80)
    suitable_occasions: list[str] | None = Field(default=None, max_length=20)
    compatible_aesthetics: list[str] | None = Field(default=None, max_length=20)
    seasons: list[str] | None = Field(default=None, max_length=4)
    laundry_status: str | None = Field(
        default=None, pattern="^(clean|dirty|in_laundry)$"
    )
    is_available: bool | None = None
    is_favorite: bool | None = None


class ItemRead(ItemFields):
    model_config = ConfigDict(from_attributes=True)

    id: str
    image_path: str | None
    last_worn: datetime | None
    times_worn: int
    created_at: datetime
    updated_at: datetime
