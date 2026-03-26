import pytest
from django.contrib.auth.models import User
from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def seeded_user(db):
    return User.objects.create_user(
        username="seeded-user",
        email="seeded@example.com",
        password="seededpass123",
    )
