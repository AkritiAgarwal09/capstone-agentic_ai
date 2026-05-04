FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
RUN uv pip install --system \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.32.0" \
    "pydantic-ai>=1.0.0" \
    "pymupdf>=1.24.0" \
    "httpx>=0.27.0" \
    "python-multipart>=0.0.12" \
    "pydantic>=2.8.0"

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
