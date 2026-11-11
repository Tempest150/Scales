# Scales API (Quart) — dev image.
# requirements.txt was generated against Python 3.13.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Bind on all interfaces so the port is reachable from outside the container.
ENV API_HOST=0.0.0.0 \
    API_PORT=5010
EXPOSE 5010

# app.run(debug=True) gives auto-reload when the source is bind-mounted (see docker-compose.yml).
CMD ["python", "app.py"]
