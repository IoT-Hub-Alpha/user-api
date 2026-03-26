import os

from django.core.management import execute_from_command_line

from app.core.config import settings


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    execute_from_command_line(["manage.py", "migrate"])
    execute_from_command_line(["manage.py", "setup_roles", "--skip-users"])
    execute_from_command_line(
        ["manage.py", "runserver", f"{settings.host}:{settings.port}", "--noreload"]
    )


if __name__ == "__main__":
    main()
