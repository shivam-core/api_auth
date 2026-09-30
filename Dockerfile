FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ /app/backend/
COPY --from=frontend /build/dist /app/frontend/dist
COPY start.sh /app/start.sh
RUN useradd --create-home appuser
USER appuser
WORKDIR /app/backend
EXPOSE 8000
CMD ["sh", "/app/start.sh"]
