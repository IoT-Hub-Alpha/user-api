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

## Running Against `postgresql-platform`

If this service uses the shared PostgreSQL platform, point Django at the
service-owned `users` schema:

```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=iot_hub_platform
DB_HOST=localhost
DB_PORT=5432
DB_USER=users_user
DB_PASSWORD=users_change_me
DB_SCHEMA=users
```

In that mode, `postgresql-platform` provides the database server, but `user-api`
owns its own schema and Django auth tables inside that schema.

Before the first migration run, make sure the service database role can either:

- create schemas in `iot_hub_platform`, or
- use a schema that was created and assigned by a PostgreSQL admin

Example admin SQL:

```sql
CREATE ROLE users_user LOGIN PASSWORD 'users_change_me';
GRANT CONNECT, CREATE ON DATABASE iot_hub_platform TO users_user;
```

For an explicit one-by-one bootstrap flow, run:

```bash
python manage.py ensure_db_schema
python manage.py migrate
python manage.py setup_roles
python -m app.main
```

This is the intended pattern for other services too:

1. PostgreSQL is up
2. service schema exists
3. service migrations run
4. service bootstrap runs if needed
5. service API starts

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
