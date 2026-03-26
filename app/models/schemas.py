from dataclasses import dataclass


@dataclass(frozen=True)
class RoleDescriptor:
    api_name: str
    group_name: str | None
    is_superuser: bool


ROLE_MAP = {
    "admin": RoleDescriptor(
        api_name="admin",
        group_name=None,
        is_superuser=True,
    ),
    "operator": RoleDescriptor(
        api_name="operator",
        group_name="Operators",
        is_superuser=False,
    ),
    "viewer": RoleDescriptor(
        api_name="viewer",
        group_name="Viewers",
        is_superuser=False,
    ),
}
