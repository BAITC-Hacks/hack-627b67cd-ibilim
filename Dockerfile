FROM node:20-alpine AS web
WORKDIR /web
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY seed/ seed/
COPY --from=web /web/dist web/dist
WORKDIR /app/backend
ENV DB_PATH=/tmp/hub.db
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
