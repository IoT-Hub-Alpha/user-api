import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create default groups and optional seed users aligned with monolith roles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-superuser",
            action="store_true",
            help="Skip superuser creation",
        )
        parser.add_argument(
            "--skip-groups",
            action="store_true",
            help="Skip groups creation",
        )
        parser.add_argument(
            "--skip-users",
            action="store_true",
            help="Skip operator/viewer user creation",
        )

    def handle(self, *args, **options):
        if not options["skip_superuser"]:
            self.create_superuser()
        if not options["skip_groups"]:
            self.create_groups()
        if not options["skip_users"]:
            self.create_users()

        self.stdout.write(self.style.SUCCESS("User-api role bootstrap completed."))

    def create_superuser(self):
        username = os.getenv("ADMIN_USERNAME", "admin")
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("ADMIN_PASSWORD", "admin123")

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" already exists.')
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f'Created superuser "{username}".'))

    def create_groups(self):
        for name in ("Operators", "Viewers"):
            Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Groups ensured: Operators, Viewers"))

    def create_users(self):
        defaults = [
            {
                "username": os.getenv("OPERATOR_USERNAME", "operator"),
                "email": os.getenv("OPERATOR_EMAIL", "operator@example.com"),
                "password": os.getenv("OPERATOR_PASSWORD", "operator123"),
                "group": "Operators",
            },
            {
                "username": os.getenv("VIEWER_USERNAME", "viewer"),
                "email": os.getenv("VIEWER_EMAIL", "viewer@example.com"),
                "password": os.getenv("VIEWER_PASSWORD", "viewer123"),
                "group": "Viewers",
            },
        ]

        for user_data in defaults:
            username = user_data["username"]
            group_name = user_data["group"]

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User "{username}" already exists.')
                )
                continue

            group, _ = Group.objects.get_or_create(name=group_name)
            user = User.objects.create_user(
                username=username,
                email=user_data["email"],
                password=user_data["password"],
                is_staff=True,
            )
            user.groups.add(group)
            self.stdout.write(
                self.style.SUCCESS(f'Created "{username}" in group "{group_name}".')
            )
