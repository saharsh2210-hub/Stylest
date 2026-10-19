from collections import Counter
from io import BytesIO
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from PIL import Image, UnidentifiedImageError
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR
from app.db.database import get_db
from app.models.wardrobe import WardrobeItem
from app.schemas.wardrobe import ItemCreate, ItemRead, ItemUpdate

router = APIRouter(tags=["wardrobe"])
MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


def _save_image(upload: UploadFile, item_id: str) -> tuple[str, bytes | None, str | None]:
    contents = upload.file.read(MAX_IMAGE_BYTES + 1)
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Images must be 8 MB or smaller.")
    try:
        with Image.open(BytesIO(contents)) as image:
            image.verify()
            image_format = image.format or ""
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=415, detail="Upload a valid JPEG, PNG, or WebP image.") from exc
    extension = ALLOWED_IMAGE_FORMATS.get(image_format)
    if not extension:
        raise HTTPException(status_code=415, detail="Upload a valid JPEG, PNG, or WebP image.")
    if os.getenv("FITCHECK_IMAGE_STORAGE", "local").lower() == "database":
        try:
            with Image.open(BytesIO(contents)) as image:
                image.load()
                has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                optimized = BytesIO()
                image.save(optimized, format="WEBP", quality=82, method=6)
        except (UnidentifiedImageError, OSError) as exc:
            raise HTTPException(status_code=415, detail="Could not safely process this image.") from exc
        return f"/api/wardrobe/{item_id}/image", optimized.getvalue(), "image/webp"
    filename = f"{uuid4().hex}{extension}"
    path = UPLOAD_DIR / filename
    path.write_bytes(contents)
    return f"/uploads/{filename}", None, None


def _item_or_404(db: Session, item_id: str) -> WardrobeItem:
    item = db.get(WardrobeItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Wardrobe item not found.")
    return item


@router.get("/wardrobe", response_model=list[ItemRead])
def list_items(
    search: str | None = None,
    category: str | None = None,
    color: str | None = None,
    fit: str | None = None,
    aesthetic: str | None = None,
    laundry_status: str | None = None,
    favorite: bool | None = None,
    sort: str = Query(default="newest", pattern="^(newest|name|most_worn)$"),
    db: Session = Depends(get_db),
):
    query = select(WardrobeItem)
    if search:
        query = query.where(WardrobeItem.name.ilike(f"%{search.strip()}%"))
    if category:
        query = query.where(WardrobeItem.category == category)
    if color:
        query = query.where(WardrobeItem.primary_color == color)
    if fit:
        query = query.where(WardrobeItem.fit == fit)
    if laundry_status:
        query = query.where(WardrobeItem.laundry_status == laundry_status)
    if favorite is not None:
        query = query.where(WardrobeItem.is_favorite == favorite)
    ordering = {
        "newest": WardrobeItem.created_at.desc(),
        "name": WardrobeItem.name.asc(),
        "most_worn": WardrobeItem.times_worn.desc(),
    }
    items = db.scalars(query.order_by(ordering[sort])).all()
    if aesthetic:
        items = [
            item
            for item in items
            if aesthetic in item.compatible_aesthetics
        ]
    return items


@router.post("/wardrobe", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = WardrobeItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/wardrobe/upload", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def upload_item(
    file: UploadFile = File(...),
    name: str = Query(min_length=1, max_length=120),
    category: str = Query(min_length=1, max_length=40),
    primary_color: str = Query(default="Unspecified", max_length=40),
    db: Session = Depends(get_db),
):
    item_id = str(uuid4())
    path, image_data, image_content_type = _save_image(file, item_id)
    item = WardrobeItem(
        id=item_id,
        name=name,
        category=category,
        primary_color=primary_color,
        image_path=path,
        image_data=image_data,
        image_content_type=image_content_type,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/wardrobe/upload-multiple", status_code=status.HTTP_201_CREATED)
def upload_multiple(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files or len(files) > 20:
        raise HTTPException(status_code=400, detail="Choose between 1 and 20 images.")
    created = []
    for file in files:
        item_id = str(uuid4())
        image_path, image_data, image_content_type = _save_image(file, item_id)
        name = Path(file.filename or "New clothing item").stem[:120] or "New clothing item"
        item = WardrobeItem(
            id=item_id,
            name=name,
            category="Other accessories",
            image_path=image_path,
            image_data=image_data,
            image_content_type=image_content_type,
        )
        db.add(item)
        created.append(item)
    db.commit()
    for item in created:
        db.refresh(item)
    return created


@router.get("/wardrobe/stats")
def wardrobe_stats(db: Session = Depends(get_db)):
    items = db.scalars(select(WardrobeItem)).all()
    statuses = {key: sum(item.laundry_status == key for item in items) for key in ("clean", "dirty", "in_laundry")}
    colors = Counter(item.primary_color for item in items)
    return {
        "total": len(items),
        "clean": statuses["clean"],
        "dirty": statuses["dirty"],
        "in_laundry": statuses["in_laundry"],
        "favorites": sum(item.is_favorite for item in items),
        "colors": [{"name": name, "count": count} for name, count in colors.most_common(8)],
    }


@router.get("/wardrobe/{item_id}/image", response_class=Response)
def get_item_image(item_id: str, db: Session = Depends(get_db)):
    item = _item_or_404(db, item_id)
    if not item.image_data or not item.image_content_type:
        raise HTTPException(status_code=404, detail="This item has no database-stored image.")
    return Response(
        content=item.image_data,
        media_type=item.image_content_type,
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.get("/wardrobe/{item_id}", response_model=ItemRead)
def get_item(item_id: str, db: Session = Depends(get_db)):
    return _item_or_404(db, item_id)


@router.patch("/wardrobe/{item_id}", response_model=ItemRead)
def update_item(item_id: str, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = _item_or_404(db, item_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/wardrobe/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, db: Session = Depends(get_db)):
    item = _item_or_404(db, item_id)
    db.delete(item)
    db.commit()
