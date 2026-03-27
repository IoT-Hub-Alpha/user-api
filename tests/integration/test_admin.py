import pytest
from django.contrib.auth.models import User


@pytest.mark.django_db
def test_admin_add_user_form_shows_email_field(client):
    admin_user = User.objects.create_superuser(
        username="admin-test",
        email="admin-test@example.com",
        password="adminpass123",
    )
    client.force_login(admin_user)

    response = client.get("/admin/auth/user/add/")

    assert response.status_code == 200
    assert b'name="email"' in response.content


@pytest.mark.django_db
def test_admin_add_user_form_saves_email(client):
    admin_user = User.objects.create_superuser(
        username="admin-save",
        email="admin-save@example.com",
        password="adminpass123",
    )
    client.force_login(admin_user)

    response = client.post(
        "/admin/auth/user/add/",
        data={
            "username": "created-in-admin",
            "email": "created-in-admin@example.com",
            "usable_password": "true",
            "password1": "strongpass123",
            "password2": "strongpass123",
        },
        follow=True,
    )

    assert response.status_code == 200
    created_user = User.objects.get(username="created-in-admin")
    assert created_user.email == "created-in-admin@example.com"
