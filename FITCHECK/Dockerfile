FROM node:24-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    FITCHECK_ENV=production \
    FITCHECK_IMAGE_STORAGE=database \
    FITCHECK_FRONTEND_DIST=/app/frontend/dist \
    FITCHECK_CORS_ORIGINS=""

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=frontend-build /build/frontend/dist /app/frontend/dist

EXPOSE 10000
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
