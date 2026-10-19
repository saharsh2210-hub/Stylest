from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, outfits, wardrobe
from app.core.auth import auth_enabled, validate_production_auth, verify_session_token
from app.core.config import FRONTEND_DIST, UPLOAD_DIR
from app.db.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    validate_production_auth()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FITCHECK API",
    description="Personal wardrobe and outfit stylist",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "FITCHECK_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.include_router(auth.router, prefix="/api")
app.include_router(wardrobe.router, prefix="/api")
app.include_router(outfits.router, prefix="/api")


@app.middleware("http")
async def protect_private_api(request, call_next):
    if (
        request.url.path.startswith("/api/")
        and request.url.path not in {"/api/auth/login", "/api/auth/session"}
        and request.method != "OPTIONS"
        and auth_enabled()
        and not verify_session_token(request.cookies.get("fitcheck_session"))
    ):
        return JSONResponse({"detail": "Please sign in to access your wardrobe."}, status_code=401)
    return await call_next(request)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def home():
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
    return {"message": "Welcome to FITCHECK API!", "status": "running"}


@app.get("/{page_path:path}", include_in_schema=False)
def frontend_page(page_path: str):
    index = FRONTEND_DIST / "index.html"
    if not index.is_file():
        return JSONResponse({"detail": "Not found"}, status_code=404)
    requested_file = (FRONTEND_DIST / page_path).resolve()
    if requested_file.is_relative_to(FRONTEND_DIST.resolve()) and requested_file.is_file():
        return FileResponse(requested_file)
    if Path(page_path).suffix:
        return JSONResponse({"detail": "Not found"}, status_code=404)
    return FileResponse(index)
