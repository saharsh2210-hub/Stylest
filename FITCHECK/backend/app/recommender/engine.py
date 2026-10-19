from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
import json
import math
import os
import random

from app.models.wardrobe import Outfit, WardrobeItem
from app.schemas.outfit import OutfitGenerate

DEFAULT_WEIGHTS = {
    "aesthetic": 0.30,
    "color": 0.25,
    "fit": 0.20,
    "occasion": 0.15,
    "weather_rotation": 0.10,
}


def _load_weights() -> dict[str, float]:
    raw_weights = os.getenv("FITCHECK_SCORING_WEIGHTS")
    if not raw_weights:
        return DEFAULT_WEIGHTS.copy()
    try:
        configured = json.loads(raw_weights)
    except json.JSONDecodeError as exc:
        raise ValueError("FITCHECK_SCORING_WEIGHTS must be a JSON object.") from exc
    if not isinstance(configured, dict) or set(configured) != set(DEFAULT_WEIGHTS):
        raise ValueError(
            "FITCHECK_SCORING_WEIGHTS must define aesthetic, color, fit, occasion, and weather_rotation."
        )
    values = {key: float(value) for key, value in configured.items()}
    if any(not math.isfinite(value) or value < 0 for value in values.values()):
        raise ValueError("FITCHECK_SCORING_WEIGHTS values must be finite and non-negative.")
    total = sum(values.values())
    if total <= 0:
        raise ValueError("At least one FITCHECK_SCORING_WEIGHTS value must be positive.")
    return {key: value / total for key, value in values.items()}


WEIGHTS = _load_weights()
TOPS = {"shirts", "t-shirts", "t shirts", "polo shirts", "hoodies", "sweaters"}
BOTTOMS = {"jeans", "formal trousers", "cargo pants", "shorts"}
SHOES = {"sneakers", "formal shoes", "boots"}
NEUTRALS = {"black", "white", "gray", "grey", "navy", "beige", "cream", "brown", "denim"}


@dataclass
class Recommendation:
    item_ids: list[str]
    score: float
    explanation: list[str]


class InsufficientWardrobe(ValueError):
    def __init__(self, missing: list[str]):
        self.missing = missing
        super().__init__(f"Add clean, suitable {' and '.join(missing)} to generate an outfit.")


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _category_group(item: WardrobeItem) -> str | None:
    category = _normalize(item.category)
    subcategory = _normalize(item.subcategory)
    for group, categories in (("top", TOPS), ("bottom", BOTTOMS), ("shoes", SHOES)):
        if category in categories or subcategory in categories:
            return group
    return None


def _specific_category(item: WardrobeItem) -> str:
    category = _normalize(item.category)
    subcategory = _normalize(item.subcategory)
    known_categories = TOPS | BOTTOMS | SHOES
    if category in known_categories:
        return category
    if subcategory in known_categories:
        return subcategory
    return category


def _aesthetic_fit(items: list[WardrobeItem], aesthetic: str) -> bool:
    requested = _normalize(aesthetic)
    categories = [_specific_category(item) for item in items]
    if requested == "formal / college":
        return categories == ["shirts", "formal trousers", "formal shoes"]
    if requested == "smart casual":
        return (
            categories[0] in {"shirts", "polo shirts"}
            and categories[1] in {"jeans", "formal trousers"}
            and categories[2] in {"sneakers", "formal shoes"}
        )
    if requested == "business casual":
        return (
            categories[0] in {"shirts", "polo shirts"}
            and categories[1] == "formal trousers"
            and categories[2] in {"formal shoes", "sneakers"}
        )
    if requested == "old money":
        return (
            categories[0] in {"shirts", "polo shirts"}
            and categories[1] == "formal trousers"
            and categories[2] in {"formal shoes", "sneakers"}
        )
    if requested == "streetwear":
        return (
            categories[1] in {"jeans", "cargo pants"}
            and categories[2] == "sneakers"
            and (
                _normalize(items[0].fit) in {"oversized", "relaxed", "loose"}
                or _normalize(items[0].style) == "streetwear"
            )
        )
    return True


def _requested_season(request: OutfitGenerate) -> str | None:
    if request.season:
        return _normalize(request.season)
    aesthetic = _normalize(request.aesthetic)
    return aesthetic if aesthetic in {"summer", "winter"} else None


def _eligible(item: WardrobeItem, request: OutfitGenerate) -> bool:
    if not item.is_available or item.laundry_status != "clean" or item.id in request.exclude_item_ids:
        return False
    aesthetic = _normalize(request.aesthetic)
    if item.compatible_aesthetics and aesthetic not in {
        _normalize(value) for value in item.compatible_aesthetics
    }:
        if _normalize(item.style) not in {aesthetic, ""}:
            return False
    if item.suitable_occasions and _normalize(request.occasion) not in {
        _normalize(value) for value in item.suitable_occasions
    }:
        return False
    season = _requested_season(request)
    if season and item.seasons and season not in {
        _normalize(value) for value in item.seasons
    }:
        return False
    return True


def _color_score(items: list[WardrobeItem]) -> float:
    colors = [_normalize(item.primary_color) for item in items if _normalize(item.primary_color)]
    if len(set(colors)) <= 1:
        return 1.0
    neutral_count = sum(color in NEUTRALS for color in colors)
    secondary_colors = [_normalize(item.secondary_color) for item in items if item.secondary_color]
    if neutral_count >= len(colors) - 1:
        return 0.92
    if secondary_colors and any(color in colors for color in secondary_colors):
        return 0.86
    if len(colors) == 2:
        return 0.72
    return 0.55


def _fit_score(items: list[WardrobeItem]) -> float:
    fits = [_normalize(item.fit) for item in items]
    relaxed = {"oversized", "relaxed", "loose"}
    fitted = {"slim", "skinny", "fitted"}
    if fits[0] in relaxed and fits[1] in relaxed:
        return 0.75
    if (fits[0] in relaxed and fits[1] in fitted) or (fits[1] in relaxed and fits[0] in fitted):
        return 1.0
    return 0.84


def _aesthetic_score(items: list[WardrobeItem], aesthetic: str) -> float:
    requested = _normalize(aesthetic)
    scores = []
    for item in items:
        tags = {_normalize(tag) for tag in item.compatible_aesthetics}
        style = _normalize(item.style)
        if requested in tags or requested == style:
            scores.append(1.0)
        elif style and style in requested:
            scores.append(0.8)
        else:
            scores.append(0.65)
    if requested == "minimalist":
        scores.append(1.0 if all(_normalize(item.pattern) in {"solid", "plain"} for item in items) else 0.55)
        scores.append(1.0 if sum(_normalize(item.primary_color) not in NEUTRALS for item in items) <= 1 else 0.5)
    if requested == "monochrome":
        scores.append(1.0 if len({_normalize(item.primary_color) for item in items}) <= 1 else 0.35)
    if requested == "old money":
        scores.append(1.0 if _specific_category(items[2]) == "formal shoes" else 0.75)
    return sum(scores) / len(scores)


def _combination_score(
    items: list[WardrobeItem], request: OutfitGenerate, previous: list[Outfit]
) -> tuple[float, list[str]]:
    aesthetic = _aesthetic_score(items, request.aesthetic)
    color = _color_score(items)
    fit = _fit_score(items)
    occasion = sum(
        not item.suitable_occasions
        or _normalize(request.occasion) in {_normalize(value) for value in item.suitable_occasions}
        for item in items
    ) / len(items)
    season = _requested_season(request)
    weather = sum(
        not season
        or not item.seasons
        or season in {_normalize(value) for value in item.seasons}
        for item in items
    ) / len(items)
    now = datetime.now(timezone.utc)
    recent_wear = sum(
        max(
            min(item.times_worn, 8) / 8,
            min(
                1,
                max(
                    0,
                    1
                    - (
                        now
                        - (
                            item.last_worn.replace(tzinfo=timezone.utc)
                            if item.last_worn and item.last_worn.tzinfo is None
                            else item.last_worn
                        )
                    ).days
                    / 14,
                ),
            )
            if item.last_worn
            else 0,
        )
        for item in items
    ) / len(items)
    raw = (
        aesthetic * WEIGHTS["aesthetic"]
        + color * WEIGHTS["color"]
        + fit * WEIGHTS["fit"]
        + occasion * WEIGHTS["occasion"]
        + weather * WEIGHTS["weather_rotation"] * 0.5
        + (1 - recent_wear) * WEIGHTS["weather_rotation"] * 0.5
    ) * 100
    ids = {item.id for item in items}
    repeated = sum(set(outfit.item_ids) == ids for outfit in previous)
    recency_penalty = min(repeated, 3) * 12
    score = max(0.0, min(100.0, raw - recency_penalty))
    explanations = [
        f"{request.aesthetic} styling informed the silhouette and item selection.",
        f"{items[0].primary_color} and {items[1].primary_color} create a considered color palette.",
        f"Selected for {request.occasion.lower()} and balanced proportions.",
    ]
    if season:
        explanations.append(f"Season suitability was checked for {season}.")
    return score, explanations


def recommend(
    wardrobe: list[WardrobeItem], request: OutfitGenerate, history: list[Outfit]
) -> Recommendation:
    candidates = [item for item in wardrobe if _eligible(item, request)]
    groups = {
        group: [item for item in candidates if _category_group(item) == group]
        for group in ("top", "bottom", "shoes")
    }
    missing = [label for key, label in (("top", "tops"), ("bottom", "bottoms"), ("shoes", "shoes")) if not groups[key]]
    if missing:
        raise InsufficientWardrobe(missing)

    grouped_history = Counter(tuple(sorted(outfit.item_ids)) for outfit in history)
    ranked: list[tuple[float, list[WardrobeItem], list[str], bool]] = []
    optional = [
        item
        for item in candidates
        if item.category.lower() in {"belts", "watches", "other accessories"}
        or (
            item.category.lower() == "jackets"
            and _requested_season(request) in {"autumn", "winter"}
        )
    ]
    for top, bottom, shoes in product(groups["top"], groups["bottom"], groups["shoes"]):
        pieces = [top, bottom, shoes]
        if not _aesthetic_fit(pieces, request.aesthetic):
            continue
        variants = [pieces]
        variants.extend(
            pieces + [accessory]
            for accessory in optional
            if accessory.id not in {piece.id for piece in pieces}
        )
        for variant in variants:
            score, reasons = _combination_score(variant, request, history)
            key = tuple(sorted(item.id for item in variant))
            ranked.append((score, variant, reasons, grouped_history[key] > 0))

    if not ranked:
        if _normalize(request.aesthetic) == "formal / college":
            raise InsufficientWardrobe(["button-down shirts", "formal trousers", "formal shoes"])
        raise InsufficientWardrobe(["tops, bottoms, or shoes suited to this aesthetic"])
    unseen = [candidate for candidate in ranked if not candidate[3]]
    pool = unseen or ranked
    pool.sort(key=lambda candidate: candidate[0], reverse=True)
    top_score = pool[0][0]
    strongest = [candidate for candidate in pool if candidate[0] >= top_score - 8][:8]
    rng = random.Random(request.seed)
    score, chosen, explanations, _ = rng.choice(strongest)
    return Recommendation([item.id for item in chosen], round(score, 1), explanations)
