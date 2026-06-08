FROM python:3.11-slim

WORKDIR /app
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_DEFAULT_TIMEOUT=120
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_DEFAULT_TIMEOUT=${PIP_DEFAULT_TIMEOUT}
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY alembic.ini .
COPY migrations ./migrations

EXPOSE 8000
CMD ["sh", "-c", "python -m app.migration_runner && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
