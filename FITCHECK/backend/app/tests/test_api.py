from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes import wardrobe as wardrobe_routes
from app.db.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    test_session = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()


def add_item(client: TestClient, name: str, category: str, **fields):
    response = client.post(
        "/api/wardrobe",
        json={"name": name, "category": category, **fields},
    )
    assert response.status_code == 201
    return response.json()


def test_empty_wardrobe_is_empty_and_requires_real_clothes(client: TestClient):
    assert client.get("/api/wardrobe").json() == []
    assert client.get("/api/wardrobe/stats").json()["total"] == 0
    response = client.post(
        "/api/outfits/generate",
        json={"aesthetic": "Casual", "occasion": "Everyday"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["missing"] == ["tops", "bottoms", "shoes"]


def test_wardrobe_crud_filters_and_laundry(client: TestClient):
    item = add_item(
        client,
        "Canvas overshirt",
        "Shirts",
        primary_color="Navy",
        compatible_aesthetics=["Casual"],
    )
    assert client.get("/api/wardrobe?category=Shirts&color=Navy").json()[0]["id"] == item["id"]
    updated = client.patch(
        f"/api/wardrobe/{item['id']}",
        json={"is_favorite": True, "laundry_status": "dirty"},
    )
    assert updated.status_code == 200
    assert updated.json()["is_favorite"] is True
    assert client.get("/api/wardrobe?laundry_status=dirty").json()[0]["name"] == "Canvas overshirt"
    assert client.delete(f"/api/wardrobe/{item['id']}").status_code == 204
    assert client.get("/api/wardrobe").json() == []


def test_recommendations_use_clean_owned_items_and_rotate(client: TestClient):
    first_top = add_item(client, "White tee", "T-shirts", primary_color="White", fit="Regular")
    second_top = add_item(client, "Black tee", "T-shirts", primary_color="Black", fit="Regular")
    first_bottom = add_item(client, "Blue denim", "Jeans", primary_color="Denim")
    second_bottom = add_item(client, "Black denim", "Jeans", primary_color="Black")
    shoes = add_item(client, "Canvas sneakers", "Sneakers", primary_color="White")
    dirty_top = add_item(
        client,
        "Dirty shirt",
        "Shirts",
        primary_color="Red",
        laundry_status="dirty",
    )

    request = {"aesthetic": "Casual", "occasion": "Everyday", "seed": 7}
    first = client.post("/api/outfits/generate", json=request)
    assert first.status_code == 201
    assert first.json()["score"] <= 100
    assert first.json()["score"] >= 0
    assert len(first.json()["item_ids"]) == len(set(first.json()["item_ids"]))
    assert dirty_top["id"] not in first.json()["item_ids"]
    assert shoes["id"] in first.json()["item_ids"]
    assert any(item_id in {first_top["id"], second_top["id"]} for item_id in first.json()["item_ids"])
    assert any(item_id in {first_bottom["id"], second_bottom["id"]} for item_id in first.json()["item_ids"])

    second = client.post("/api/outfits/generate", json=request)
    assert second.status_code == 201
    assert set(second.json()["item_ids"]) != set(first.json()["item_ids"])


def test_specific_aesthetic_requires_compatible_categories(client: TestClient):
    add_item(client, "Polo", "Polo shirts")
    add_item(client, "Denim", "Jeans")
    add_item(client, "Trainers", "Sneakers")
    response = client.post(
        "/api/outfits/generate",
        json={"aesthetic": "Formal / College", "occasion": "College"},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["missing"] == [
        "button-down shirts",
        "formal trousers",
        "formal shoes",
    ]


def test_unavailable_and_explicitly_excluded_items_are_not_recommended(client: TestClient):
    top = add_item(client, "White tee", "T-shirts", is_available=False)
    add_item(client, "Blue denim", "Jeans")
    add_item(client, "Canvas sneakers", "Sneakers")
    request = {"aesthetic": "Casual", "occasion": "Everyday"}
    assert client.post("/api/outfits/generate", json=request).json()["detail"]["missing"] == ["tops"]

    client.patch(f"/api/wardrobe/{top['id']}", json={"is_available": True})
    request["exclude_item_ids"] = [top["id"]]
    response = client.post("/api/outfits/generate", json=request)
    assert response.status_code == 422
    assert response.json()["detail"]["missing"] == ["tops"]


def test_marking_outfit_worn_updates_item_history(client: TestClient):
    top = add_item(client, "Oxford shirt", "Shirts")
    bottom = add_item(client, "Tailored trousers", "Formal trousers")
    shoes = add_item(client, "Derbies", "Formal shoes")
    generated = client.post(
        "/api/outfits/generate",
        json={"aesthetic": "Formal / College", "occasion": "Work"},
    ).json()

    assert set(generated["item_ids"]) == {top["id"], bottom["id"], shoes["id"]}
    worn = client.patch(f"/api/outfits/{generated['id']}/worn")
    assert worn.status_code == 200
    assert worn.json()["status"] == "worn"
    assert client.get("/api/wardrobe?sort=most_worn").json()[0]["times_worn"] == 1
    assert client.get("/api/outfits?status_filter=worn").json()[0]["id"] == generated["id"]


def test_outfit_can_be_saved_favorited_and_planned(client: TestClient):
    add_item(client, "Oxford shirt", "Shirts")
    add_item(client, "Tailored trousers", "Formal trousers")
    add_item(client, "Derbies", "Formal shoes")
    generated = client.post(
        "/api/outfits/generate",
        json={"aesthetic": "Formal / College", "occasion": "Work"},
    ).json()

    saved = client.patch(f"/api/outfits/{generated['id']}/favorite")
    assert saved.json()["is_favorite"] is True
    assert saved.json()["status"] == "saved"

    planned = client.patch(
        f"/api/outfits/{generated['id']}/plan",
        json={"planned_for": "2026-10-20"},
    )
    assert planned.json()["status"] == "planned"
    assert planned.json()["planned_for"] == "2026-10-20"
    assert client.get("/api/outfits?status_filter=planned&favorite=true").json()[0]["id"] == generated["id"]


def test_upload_validates_real_image_content_and_uses_safe_names(
    client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(wardrobe_routes, "UPLOAD_DIR", tmp_path)
    invalid = client.post(
        "/api/wardrobe/upload?name=Fake&category=Shirts",
        files={"file": ("looks.jpg", b"not an image", "image/jpeg")},
    )
    assert invalid.status_code == 415

    stream = BytesIO()
    Image.new("RGB", (8, 8), color="white").save(stream, format="PNG")
    response = client.post(
        "/api/wardrobe/upload?name=White+tee&category=T-shirts",
        files={"file": ("unsafe name.png", stream.getvalue(), "image/png")},
    )
    assert response.status_code == 201
    image_path = response.json()["image_path"]
    assert image_path.startswith("/uploads/")
    saved_file = tmp_path / image_path.rsplit("/", 1)[1]
    assert saved_file.exists()
    assert saved_file.name != "unsafe name.png"


def test_database_image_storage_survives_without_local_file_writes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    monkeypatch.setattr(wardrobe_routes, "UPLOAD_DIR", tmp_path)
    monkeypatch.setenv("FITCHECK_IMAGE_STORAGE", "database")
    stream = BytesIO()
    Image.new("RGBA", (80, 60), color=(240, 230, 210, 255)).save(stream, format="PNG")
    response = client.post(
        "/api/wardrobe/upload?name=Saved+top&category=Shirts",
        files={"file": ("saved.png", stream.getvalue(), "image/png")},
    )
    assert response.status_code == 201
    item = response.json()
    assert item["image_path"] == f"/api/wardrobe/{item['id']}/image"
    assert not list(tmp_path.iterdir())

    saved_image = client.get(item["image_path"])
    assert saved_image.status_code == 200
    assert saved_image.headers["content-type"] == "image/webp"
    assert Image.open(BytesIO(saved_image.content)).size == (80, 60)


def test_public_api_requires_password_and_uses_http_only_session_cookie(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("FITCHECK_APP_PASSWORD", "a-private-app-password-123")
    monkeypatch.setenv("FITCHECK_SESSION_SECRET", "private-test-signing-key-with-more-than-32-characters")
    assert client.get("/api/wardrobe").status_code == 401
    assert client.get("/api/auth/session").json() == {
        "authenticated": False,
        "password_required": True,
    }

    invalid = client.post("/api/auth/login", json={"password": "incorrect"})
    assert invalid.status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"password": "a-private-app-password-123"},
    )
    assert login.status_code == 200
    assert login.cookies.get("fitcheck_session")
    assert "httponly" in login.headers["set-cookie"].lower()
    assert client.get("/api/wardrobe").status_code == 200

    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/wardrobe").status_code == 401


def test_production_requires_strong_owner_password_and_session_secret(
    monkeypatch: pytest.MonkeyPatch,
):
    from app.core.auth import validate_production_auth

    monkeypatch.setenv("FITCHECK_ENV", "production")
    monkeypatch.delenv("FITCHECK_APP_PASSWORD", raising=False)
    monkeypatch.delenv("FITCHECK_SESSION_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="FITCHECK_APP_PASSWORD"):
        validate_production_auth()

    monkeypatch.setenv("FITCHECK_APP_PASSWORD", "a-private-app-password-123")
    monkeypatch.setenv("FITCHECK_SESSION_SECRET", "too-short")
    with pytest.raises(RuntimeError, match="FITCHECK_SESSION_SECRET"):
        validate_production_auth()

    monkeypatch.setenv(
        "FITCHECK_SESSION_SECRET",
        "a-long-random-test-only-session-secret-123456789",
    )
    monkeypatch.setenv("FITCHECK_IMAGE_STORAGE", "local")
    with pytest.raises(RuntimeError, match="FITCHECK_IMAGE_STORAGE=database"):
        validate_production_auth()


def test_session_tokens_reject_malformed_timestamp_cookies():
    from app.core.auth import verify_session_token

    assert verify_session_token(f"{'9' * 5000}.invalid") is False
    assert verify_session_token("not-a-token") is False
