FROM python:3.12-slim

WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/src /app/backend/src
COPY backend/alembic.ini /app/backend/alembic.ini
COPY backend/alembic /app/backend/alembic
RUN pip install --no-cache-dir -e /app/backend

ENV POLYTRADER_DATABASE_URL=sqlite:////data/polytrader.db
ENV LIVE_TRADING_ENABLED=false
VOLUME ["/data"]
EXPOSE 8000
CMD ["uvicorn", "polytrader.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
