import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_setup_roles_command_creates_default_groups_and_users(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "command-admin")
    monkeypatch.setenv("ADMIN_EMAIL", "command-admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "command-admin-pass")
    monkeypatch.setenv("OPERATOR_USERNAME", "command-operator")
    monkeypatch.setenv("OPERATOR_EMAIL", "command-operator@example.com")
    monkeypatch.setenv("OPERATOR_PASSWORD", "command-operator-pass")
    monkeypatch.setenv("VIEWER_USERNAME", "command-viewer")
    monkeypatch.setenv("VIEWER_EMAIL", "command-viewer@example.com")
    monkeypatch.setenv("VIEWER_PASSWORD", "command-viewer-pass")

    call_command("setup_roles")

    from django.contrib.auth.models import Group, User

    assert User.objects.get(username="command-admin").is_superuser is True
    assert Group.objects.filter(name="Operators").exists() is True
    assert Group.objects.filter(name="Viewers").exists() is True
    assert (
        User.objects.get(username="command-operator")
        .groups.filter(name="Operators")
        .exists()
    )
    assert (
        User.objects.get(username="command-viewer")
        .groups.filter(name="Viewers")
        .exists()
    )


@pytest.mark.django_db
def test_setup_roles_command_respects_skip_flags():
    call_command("setup_roles", "--skip-superuser", "--skip-groups", "--skip-users")

    from django.contrib.auth.models import Group, User

    assert User.objects.count() == 0
    assert Group.objects.count() == 0
