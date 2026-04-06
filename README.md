# user-api

Standalone Django microservice for user CRUD and role management.

Current defaults:
- runs on port `8013`
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
python manage.py migrate
python manage.py setup_roles
python -m app.main
```

`python -m app.main` starts the API only. Schema creation, migrations, and role
bootstrap are explicit steps and should be run separately.


For an explicit one-by-one bootstrap flow, run:

```bash
python manage.py ensure_db_schema
python manage.py migrate
python manage.py setup_roles
python -m app.main
```


## Docker run

```bash
docker build -t user-api .
docker run --rm -p 8013:8013 user-api
```

`/ready/` returns `503` until the database is reachable and all migrations have
been applied.

## Project Structure

```text
app/api         HTTP views, urls, and management commands
app/services    business logic
app/models      role/schema definitions
app/core        service config and health views
config/         Django settings and URL config
tests/          root integration/unit tests
```
