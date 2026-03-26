# user-api

Standalone Django microservice for user CRUD and role management.
The repo structure is aligned to the team `Service-Template`, while preserving Django internals that fit the monolith extraction context.

Current defaults:
- standalone project outside the monolith repo
- runs on port `8013`
- supports SQLite for isolated bootstrap and PostgreSQL via env
- role model matches the monolith:
  - `admin` -> `is_superuser=True`
  - `operator` -> `Operators` group
  - `viewer` -> `Viewers` group

## Monolith Context

This service keeps the monolith's user and role semantics:
- Django built-in `User`
- `Admin` stays a Django superuser
- `Operators` and `Viewers` stay Django groups
- API remains under `/api/v1/...`

It is intended to become the extracted user domain service while preserving the product behavior users already know from the monolith.

## Endpoints

- `GET /health/`
- `GET /ready/`
- `GET /api/v1/users/`
- `POST /api/v1/users/`
- `GET /api/v1/users/{id}/`
- `PUT /api/v1/users/{id}/`
- `PATCH /api/v1/users/{id}/`
- `DELETE /api/v1/users/{id}/`
- `PUT /api/v1/users/{id}/role/`
- `GET /api/v1/roles/`

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

For the gateway team, the relevant integration data is:

- service name: `user-api`
- internal port: `8013`
- health: `/health/`
- readiness: `/ready/`
- users base URL: `http://user-api:8013/api/v1/users`
- roles base URL: `http://user-api:8013/api/v1/roles`

If the gateway uses a service registry, it needs entries for `users` and `roles` that point to those base URLs.
