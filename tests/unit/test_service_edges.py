import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from app.services.user_service import (
    ConflictError,
    NotFoundError,
    ValidationError,
    ensure_unique,
    get_user_or_404,
    normalize_payload,
    paginated_users,
    parse_json_body,
    resolve_role,
    update_user,
    validate_role,
)


@pytest.mark.django_db
def test_parse_json_body_rejects_invalid_json():
    request = RequestFactory().post(
        "/v1/users/",
        data="{not-json}",
        content_type="application/json",
    )

    with pytest.raises(ValidationError, match="Invalid JSON body"):
        parse_json_body(request)


@pytest.mark.django_db
def test_resolve_role_returns_admin_for_superuser():
    user = User.objects.create_superuser(
        username="admin-role",
        email="admin-role@example.com",
        password="adminpass123",
    )

    assert resolve_role(user) == "admin"


@pytest.mark.django_db
def test_paginated_users_rejects_invalid_page_values():
    with pytest.raises(ValidationError, match="positive integers"):
        paginated_users(page=0, page_size=10)


@pytest.mark.django_db
def test_paginated_users_rejects_page_out_of_range():
    User.objects.create_user(
        username="page-user",
        email="page-user@example.com",
        password="pagepass123",
    )

    with pytest.raises(ValidationError, match="Invalid pagination parameters"):
        paginated_users(page=2, page_size=10)


@pytest.mark.django_db
def test_get_user_or_404_raises_for_missing_user():
    with pytest.raises(NotFoundError, match="User not found"):
        get_user_or_404(99999)


@pytest.mark.django_db
def test_validate_role_rejects_unknown_role():
    with pytest.raises(ValidationError, match="Invalid role"):
        validate_role("boss")


@pytest.mark.django_db
def test_ensure_unique_rejects_duplicate_email():
    User.objects.create_user(
        username="existing-email",
        email="duplicate@example.com",
        password="pass12345",
    )

    with pytest.raises(ConflictError, match="Email already exists"):
        ensure_unique("new-user", "duplicate@example.com")


@pytest.mark.django_db
def test_normalize_payload_requires_fields_for_non_partial():
    with pytest.raises(ValidationError) as exc_info:
        normalize_payload({"username": "only-name"}, partial=False)

    assert exc_info.value.detail == {
        "email": "This field is required.",
        "password": "This field is required.",
        "role": "This field is required.",
    }


@pytest.mark.django_db
def test_normalize_payload_rejects_blank_username_on_partial_update():
    with pytest.raises(ValidationError) as exc_info:
        normalize_payload({"username": "   "}, partial=True)

    assert exc_info.value.detail == {"username": "This field may not be blank."}


@pytest.mark.django_db
def test_normalize_payload_rejects_blank_email_on_partial_update():
    with pytest.raises(ValidationError) as exc_info:
        normalize_payload({"email": "   "}, partial=True)

    assert exc_info.value.detail == {"email": "This field may not be blank."}


@pytest.mark.django_db
def test_update_user_replaces_fields_and_password():
    user = User.objects.create_user(
        username="replace-me",
        email="replace@example.com",
        password="oldpass123",
        first_name="Old",
        last_name="Name",
    )

    updated = update_user(
        user,
        {
            "username": "updated-user",
            "email": "updated@example.com",
            "password": "newpass123",
            "first_name": "New",
            "last_name": "User",
            "role": "viewer",
            "is_active": False,
        },
        partial=False,
    )

    assert updated.username == "updated-user"
    assert updated.email == "updated@example.com"
    assert updated.first_name == "New"
    assert updated.last_name == "User"
    assert updated.is_active is False
    assert updated.check_password("newpass123") is True
    assert resolve_role(updated) == "viewer"


@pytest.mark.django_db
def test_update_user_partial_keeps_existing_values():
    user = User.objects.create_user(
        username="partial-user",
        email="partial@example.com",
        password="partialpass123",
        first_name="Before",
        last_name="State",
    )

    updated = update_user(
        user,
        {
            "first_name": "After",
        },
        partial=True,
    )

    assert updated.username == "partial-user"
    assert updated.email == "partial@example.com"
    assert updated.first_name == "After"
    assert updated.last_name == "State"
    assert updated.check_password("partialpass123") is True


