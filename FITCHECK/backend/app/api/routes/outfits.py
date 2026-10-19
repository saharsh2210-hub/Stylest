from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.wardrobe import Outfit, WardrobeItem
from app.recommender.engine import InsufficientWardrobe, recommend
from app.schemas.outfit import OutfitAction, OutfitGenerate, OutfitRead

router = APIRouter(tags=["outfits"])


def _outfit_or_404(db: Session, outfit_id: str) -> Outfit:
    outfit = db.get(Outfit, outfit_id)
    if outfit is None:
        raise HTTPException(status_code=404, detail="Outfit not found.")
    return outfit


@router.get("/outfits", response_model=list[OutfitRead])
def list_outfits(status_filter: str | None = None, favorite: bool | None = None, db: Session = Depends(get_db)):
    query = select(Outfit)
    if status_filter:
        query = query.where(Outfit.status == status_filter)
    if favorite is not None:
        query = query.where(Outfit.is_favorite == favorite)
    ordering = (
        Outfit.worn_at.desc()
        if status_filter == "worn"
        else Outfit.planned_for.asc()
        if status_filter == "planned"
        else Outfit.created_at.desc()
    )
    return db.scalars(query.order_by(ordering)).all()


@router.post("/outfits/generate", response_model=OutfitRead, status_code=status.HTTP_201_CREATED)
def generate_outfit(payload: OutfitGenerate, db: Session = Depends(get_db)):
    wardrobe = db.scalars(select(WardrobeItem)).all()
    history = db.scalars(select(Outfit).order_by(Outfit.created_at.desc()).limit(100)).all()
    try:
        recommendation = recommend(wardrobe, payload, history)
    except InsufficientWardrobe as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "missing": exc.missing},
        ) from exc
    outfit = Outfit(
        id=str(uuid4()),
        item_ids=recommendation.item_ids,
        aesthetic=payload.aesthetic,
        occasion=payload.occasion,
        score=recommendation.score,
        explanation=recommendation.explanation,
    )
    db.add(outfit)
    db.commit()
    db.refresh(outfit)
    return outfit


@router.patch("/outfits/{outfit_id}/favorite", response_model=OutfitRead)
def toggle_favorite(outfit_id: str, db: Session = Depends(get_db)):
    outfit = _outfit_or_404(db, outfit_id)
    outfit.is_favorite = not outfit.is_favorite
    if outfit.status == "generated" and outfit.is_favorite:
        outfit.status = "saved"
    db.commit()
    db.refresh(outfit)
    return outfit


@router.patch("/outfits/{outfit_id}/plan", response_model=OutfitRead)
def plan_outfit(outfit_id: str, payload: OutfitAction, db: Session = Depends(get_db)):
    outfit = _outfit_or_404(db, outfit_id)
    outfit.planned_for = payload.planned_for
    outfit.status = "planned" if payload.planned_for else "saved"
    db.commit()
    db.refresh(outfit)
    return outfit


@router.patch("/outfits/{outfit_id}/worn", response_model=OutfitRead)
def mark_outfit_worn(outfit_id: str, db: Session = Depends(get_db)):
    outfit = _outfit_or_404(db, outfit_id)
    outfit.status = "worn"
    outfit.worn_at = datetime.now(timezone.utc)
    for item_id in outfit.item_ids:
        item = db.get(WardrobeItem, item_id)
        if item:
            item.times_worn += 1
            item.last_worn = outfit.worn_at
    db.commit()
    db.refresh(outfit)
    return outfit


@router.delete("/outfits/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outfit(outfit_id: str, db: Session = Depends(get_db)):
    db.delete(_outfit_or_404(db, outfit_id))
    db.commit()
