# user-api

Standalone Django microservice for user CRUD and role management.

Current defaults:
- runs on port `8013'
- role model matches the monolith:
  - `admin` -> `is_superuser=True`
  - `operator` -> `Operators` group
  - `viewer` -> `Viewers` group

## Endpoints

- `GET /health/`
- `GET /ready/`
- `GET /v1/users/`
- `POST /v1/users/`
- `GET /v1/users/{id}/`
- `PUT /v1/users/{id}/`
- `PATCH /v1/users/{id}/`
- `DELETE /v1/users/{id}/`
- `PUT /v1/users/{id}/role/`
- `GET /v1/roles/`

## Local run

```bash
cp .env.example .env
pip install -r requirements.txt -r requirements-dev.txt
python -m app.main
```

## Docker run

```bash
docker build -t user-api .
docker run --rm -p 8013:8013 user-api
```

## Project Structure

```text
app/api         HTTP views, urls, and management commands
app/services    business logic
app/models      role/schema definitions
app/core        service config and health views
config/         Django settings and URL config
tests/          root integration/unit tests
```

## Gateway Handoff

- service name: `user-api`
- internal port: `8013`
- health: `/health/`
- readiness: `/ready/`
- users base URL: `http://user-api:8013/api/v1/users`
- roles base URL: `http://user-api:8013/api/v1/roles`
