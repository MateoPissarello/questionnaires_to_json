# ==============================================================================
# Etapa 1: Compilación estática del Frontend (Next.js -> /frontend/out)
# ==============================================================================
FROM node:22-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ==============================================================================
# Etapa 2: Runtime unificado en FastAPI (Sirve API REST + Frontend estático)
# ==============================================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Instalar dependencias del Backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código del Backend y el build estático del Frontend
COPY backend/app ./app
COPY --from=frontend-builder /frontend/out ./static

EXPOSE 8000

# Ejecuta FastAPI sirviendo tanto /api/v1/... como el Frontend en /
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
