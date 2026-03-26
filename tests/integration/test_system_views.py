from unittest.mock import Mock

import pytest
from django.db import DatabaseError


@pytest.mark.django_db
def test_ready_endpoint_returns_ready(client, monkeypatch):
    ensure_connection = Mock()
    monkeypatch.setattr(
        "app.core.views.connection.ensure_connection",
        ensure_connection,
    )

    response = client.get("/ready/")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    ensure_connection.assert_called_once_with()


@pytest.mark.django_db
def test_ready_endpoint_returns_not_ready_on_database_error(client, monkeypatch):
    monkeypatch.setattr(
        "app.core.views.connection.ensure_connection",
        Mock(side_effect=DatabaseError),
    )

    response = client.get("/ready/")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


@pytest.mark.django_db
def test_list_users_rejects_non_integer_pagination(client):
    response = client.get("/api/v1/users/?page=abc&page_size=10")

    assert response.status_code == 400
    assert response.json() == {"detail": "Pagination values must be integers."}


@pytest.mark.django_db
def test_get_user_returns_not_found(client):
    response = client.get("/api/v1/users/99999/")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found."}


@pytest.mark.django_db
def test_delete_user_returns_not_found(client):
    response = client.delete("/api/v1/users/99999/")

    assert response.status_code == 404
    assert response.json() == {"detail": "User not found."}


@pytest.mark.django_db
def test_assign_role_rejects_invalid_role(client, seeded_user):
    response = client.put(
        f"/api/v1/users/{seeded_user.id}/role/",
        data='{"role": "boss"}',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]["role"]
