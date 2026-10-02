"""
Middle tier of the 3-tier stack: Flask, served by Gunicorn, talking to Postgres.

Every setting comes from an environment variable (12-factor config), so the SAME
image can run in dev, staging and prod with nothing rebuilt.
"""
import os
import socket
import time

import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "appdb")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
APP_ENV = os.environ.get("APP_ENV", "development")
HOSTNAME = socket.gethostname()


def connect(retries=1, delay=2):
    """Open a connection. Retries exist because in a container world the DB may
    still be booting when we are already running -- never assume start order."""
    last_error = None
    for _ in range(retries):
        try:
            return psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=3,
            )
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    raise last_error


def init_db():
    """Idempotent schema creation. Safe to run from every Gunicorn worker."""
    conn = connect(retries=10)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS visits (
                    id       SERIAL PRIMARY KEY,
                    hostname TEXT        NOT NULL,
                    seen_at  TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        conn.commit()
    finally:
        conn.close()


@app.get("/health")
def health():
    """LIVENESS: is this process alive? Deliberately does NOT touch the DB, so a
    database outage does not get our app container killed and restarted."""
    return jsonify(status="ok", container=HOSTNAME, env=APP_ENV), 200


@app.get("/ready")
def ready():
    """READINESS: can we actually serve traffic? This one does check the DB."""
    try:
        conn = connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        finally:
            conn.close()
        return jsonify(status="ready", db=DB_HOST), 200
    except Exception as exc:  # noqa: BLE001 - we want the reason in the body
        return jsonify(status="not-ready", db=DB_HOST, error=str(exc)), 503


@app.get("/")
def index():
    """Record a visit and report the running total, proving state lives in the
    database (which survives container deletion) and not in the container."""
    try:
        conn = connect()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO visits (hostname) VALUES (%s)", (HOSTNAME,))
                cur.execute("SELECT count(*) FROM visits")
                total = cur.fetchone()[0]
                cur.execute(
                    "SELECT hostname, seen_at FROM visits ORDER BY id DESC LIMIT 5"
                )
                recent = [
                    {"served_by": row[0], "at": row[1].isoformat()}
                    for row in cur.fetchall()
                ]
            conn.commit()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        return jsonify(error="database unreachable", detail=str(exc)), 503

    return jsonify(
        message="Hello from the app tier",
        served_by=HOSTNAME,
        env=APP_ENV,
        db_host=DB_HOST,
        total_visits=total,
        recent=recent,
    ), 200


# Runs at import time, i.e. when Gunicorn loads the module.
try:
    init_db()
except Exception as exc:  # noqa: BLE001
    print(f"[startup] schema init deferred, DB not reachable yet: {exc}", flush=True)


if __name__ == "__main__":
    # Local convenience only. In the container Gunicorn is the entrypoint.
    app.run(host="0.0.0.0", port=8000, debug=True)
