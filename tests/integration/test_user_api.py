import json

import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_health_endpoint(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_create_user(client):
    response = client.post(
        "/v1/users/",
        data=json.dumps(
            {
                "username": "operator-user",
                "email": "operator@example.com",
                "password": "operatorpass123",
                "role": "operator",
                "first_name": "Op",
                "last_name": "User",
                "is_active": True,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json()["data"]["role"] == "operator"


@pytest.mark.django_db
def test_list_users(client, seeded_user):
    response = client.get("/v1/users/?page=1&page_size=10")

    assert response.status_code == 200
    assert response.json()["pagination"]["total"] >= 1


@pytest.mark.django_db
def test_patch_user_role(client, seeded_user):
    response = client.put(
        f"/v1/users/{seeded_user.id}/role/",
        data=json.dumps({"role": "viewer"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["data"]["role"] == "viewer"


@pytest.mark.django_db
def test_delete_user(client, seeded_user):
    response = client.delete(f"/v1/users/{seeded_user.id}/")

    assert response.status_code == 204
    assert User.objects.filter(pk=seeded_user.id).exists() is False


@pytest.mark.django_db
def test_roles_endpoint(client):
    response = client.get("/v1/roles/")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert {item["name"] for item in payload} == {"admin", "operator", "viewer"}


@pytest.mark.django_db
def test_create_user_rejects_duplicate_username(client, seeded_user):
    response = client.post(
        "/v1/users/",
        data=json.dumps(
            {
                "username": seeded_user.username,
                "email": "another@example.com",
                "password": "anotherpass123",
                "role": "viewer",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 409

