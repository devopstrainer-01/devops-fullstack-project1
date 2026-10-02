# 3-Tier Web App — CI/CD with Jenkins, Docker & GHCR

A minimal 3-tier stack used as a DevOps CI/CD exercise:

- **Web tier** (`frontend/`) — nginx reverse proxy, serves `/healthz` and
  forwards everything else to the app tier.
- **App tier** (`backend/`) — Flask + Gunicorn, talks to Postgres, exposes
  `/health` (liveness) and `/ready` (readiness).
- **Data tier** — self-hosted Postgres on its own EC2 instance (not part of
  this repo).

## Infrastructure (already provisioned)

| EC2 instance   | Role                                              |
|----------------|---------------------------------------------------|
| App EC2        | Runs `frontend` + `app` containers via Docker Compose |
| DB EC2         | Self-hosted Postgres                              |
| Jenkins EC2    | Runs the CI/CD pipeline, public IP for the GitHub webhook |

## CI/CD flow

1. Push to this repo triggers a GitHub webhook → Jenkins.
2. Jenkins builds two images (`frontend`, `backend`) and pushes them to
   `ghcr.io` (GitHub Container Registry).
3. Jenkins SSHes into the App EC2 and runs `docker compose pull && up -d`
   to roll out the new images.

Full setup/reference docs: **[deployment-docs/](deployment-docs/)**.
Pipeline definition: **[Jenkinsfile](Jenkinsfile)** — fill in the `OWNER`
and `APP_EC2_HOST` placeholders before pointing a Jenkins job at it.

## Local development

```bash
cd backend && pip install -r requirements.txt
DB_HOST=localhost DB_USER=appuser DB_PASSWORD=secret python app.py
```

Or build the images directly:

```bash
docker build -t app-backend ./backend
docker build -t app-frontend ./frontend
```

## Repo layout

```
backend/            Flask app, Dockerfile, requirements.txt
frontend/            nginx config + Dockerfile (reverse proxy to the app tier)
docker-compose.yml    Production compose file, runs on the App EC2
.env.example          Template for the App EC2's runtime .env
deployment-docs/      Infra, Jenkins, GHCR, webhook & security docs
```
