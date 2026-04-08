from datetime import UTC, datetime, timedelta

import jwt
import pytest
from django.test import override_settings


def make_access_token(*, permissions: list[str]) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": "test-user-1",
        "username": "operator",
        "email": "operator@example.com",
        "groups": ["operators"],
        "permissions": permissions,
        "is_staff": True,
        "is_superuser": False,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, "test-jwt-secret", algorithm="HS256")


@pytest.mark.django_db
def test_protected_endpoint_rejects_missing_token(raw_client):
    response = raw_client.get("/v1/roles/")

    assert response.status_code == 400
    assert response.json() == {"error": "invalid token"}


@pytest.mark.django_db
def test_internal_service_header_bypasses_auth(client):
    response = client.get("/v1/roles/")

    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.django_db
@override_settings(JWT_SECRET_KEY="test-jwt-secret")
def test_valid_token_with_required_permission_is_allowed(raw_client):
    token = make_access_token(permissions=["roles.view"])

    response = raw_client.get(
        "/v1/roles/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.django_db
@override_settings(JWT_SECRET_KEY="test-jwt-secret")
def test_valid_token_without_required_permission_is_rejected(raw_client):
    token = make_access_token(permissions=["users.view"])

    response = raw_client.get(
        "/v1/roles/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Not authorized"}
