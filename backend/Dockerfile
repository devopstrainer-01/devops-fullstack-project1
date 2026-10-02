# ---- Module 1 solution: app tier image -------------------------------------
# Pin a specific minor version. "python:latest" is a moving target and will
# break your build on some random Tuesday.
FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE: no .pyc clutter in the image layer.
# PYTHONUNBUFFERED: print() reaches `docker logs` immediately instead of sitting
# in a buffer -- without this your logs look "missing".
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# curl is only here so HEALTHCHECK has something to call. Trade-off: a few MB of
# image size for a much more readable healthcheck.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# LAYER CACHE ORDER MATTERS.
# requirements.txt is copied and installed BEFORE the source code, so editing
# app.py does not invalidate the (slow) pip layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code last: this is the layer that changes on every commit.
COPY . .

# Never run as root by default. If someone escapes the app, they land as a
# nobody-user, not as uid 0.
RUN useradd --create-home --uid 1001 appuser \
 && chown -R appuser:appuser /app
USER appuser

# Pure documentation for humans and tooling. It publishes nothing by itself --
# only `-p` / `ports:` actually opens a host port.
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Exec form (JSON array): gunicorn becomes PID 1 and receives SIGTERM directly,
# so `docker stop` is a graceful shutdown instead of a 10-second kill.
# --bind 0.0.0.0:8000 is mandatory: binding to 127.0.0.1 would make the app
# unreachable from outside the container.
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "4", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
