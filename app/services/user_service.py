import logging
import json

from django.contrib.auth.models import Group, User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.http import HttpRequest

from app.models.schemas import ROLE_MAP


logger = logging.getLogger(__name__)


class ApiError(Exception):
    status_code = 400

    def __init__(self, detail):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(ApiError):
    status_code = 404


class ConflictError(ApiError):
    status_code = 409


class ValidationError(ApiError):
    status_code = 400


def parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError("Invalid JSON body.") from exc


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "role": resolve_role(user),
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def resolve_role(user: User) -> str:
    if user.is_superuser:
        return "admin"

    group_names = set(user.groups.values_list("name", flat=True))
    if "Operators" in group_names:
        return "operator"
    if "Viewers" in group_names:
        return "viewer"
    return "viewer"


def list_roles() -> list[dict]:
    return [
        {
            "name": role_name,
            "group_name": descriptor.group_name,
            "is_superuser": descriptor.is_superuser,
        }
        for role_name, descriptor in ROLE_MAP.items()
    ]


def paginated_users(page: int, page_size: int) -> dict:
    if page < 1 or page_size < 1:
        raise ValidationError("Pagination values must be positive integers.")

    queryset = User.objects.order_by("id")
    paginator = Paginator(queryset, page_size)
    try:
        page_obj = paginator.page(page)
    except (EmptyPage, PageNotAnInteger) as exc:
        raise ValidationError("Invalid pagination parameters.") from exc

    return {
        "data": [serialize_user(user) for user in page_obj.object_list],
        "pagination": {
            "page": page_obj.number,
            "page_size": page_size,
            "total": paginator.count,
            "total_pages": paginator.num_pages,
            "next_page": page_obj.next_page_number() if page_obj.has_next() else None,
            "prev_page": (
                page_obj.previous_page_number() if page_obj.has_previous() else None
            ),
        },
    }


def get_user_or_404(user_id: int) -> User:
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise NotFoundError("User not found.") from exc


def validate_role(role_name: str) -> str:
    if role_name not in ROLE_MAP:
        raise ValidationError(
            {"role": f"Invalid role. Allowed values: {', '.join(ROLE_MAP.keys())}"}
        )
    return role_name


def ensure_unique(
    username: str,
    email: str,
    excluded_user_id: int | None = None,
) -> None:
    username_qs = User.objects.filter(username=username)
    email_qs = User.objects.filter(email=email)

    if excluded_user_id is not None:
        username_qs = username_qs.exclude(pk=excluded_user_id)
        email_qs = email_qs.exclude(pk=excluded_user_id)

    if username_qs.exists():
        raise ConflictError({"username": "Username already exists."})
    if email_qs.exists():
        raise ConflictError({"email": "Email already exists."})


def normalize_payload(payload: dict, partial: bool = False) -> dict:
    required_fields = {"username", "email", "password", "role"}
    if not partial:
        missing = sorted(field for field in required_fields if not payload.get(field))
        if missing:
            raise ValidationError(
                {field: "This field is required." for field in missing}
            )

    cleaned = {
        "username": (
            payload.get("username", "").strip() if "username" in payload else None
        ),
        "email": payload.get("email", "").strip() if "email" in payload else None,
        "password": payload.get("password"),
        "first_name": payload.get("first_name", "").strip(),
        "last_name": payload.get("last_name", "").strip(),
        "is_active": payload.get("is_active"),
        "role": payload.get("role"),
    }

    if "role" in payload:
        cleaned["role"] = validate_role(payload["role"])

    blank_field_errors = {}
    for field in ("username", "email"):
        if field in payload and cleaned[field] == "":
            blank_field_errors[field] = "This field may not be blank."

    if blank_field_errors:
        raise ValidationError(blank_field_errors)

    return cleaned


def assign_role(user: User, role_name: str) -> User:
    role_name = validate_role(role_name)
    descriptor = ROLE_MAP[role_name]
    groups = []

    if descriptor.group_name is not None:
        group, _ = Group.objects.get_or_create(name=descriptor.group_name)
        groups.append(group)

    user.groups.set(groups)
    user.is_superuser = descriptor.is_superuser
    user.is_staff = True
    user.save(update_fields=["is_superuser", "is_staff"])

    logger.info(
        "User role assigned",
        extra={
            "operation": "assign_role",
            "user_id": str(user.id),
            "username": user.username,
            "role": role_name,
            "is_superuser": user.is_superuser,
        },
    )

    return user


@transaction.atomic
def create_user(payload: dict) -> User:
    cleaned = normalize_payload(payload, partial=False)
    ensure_unique(cleaned["username"], cleaned["email"])

    user = User.objects.create_user(
        username=cleaned["username"],
        email=cleaned["email"],
        password=cleaned["password"],
        first_name=cleaned["first_name"],
        last_name=cleaned["last_name"],
        is_active=True if cleaned["is_active"] is None else cleaned["is_active"],
        is_staff=True,
    )
    user = assign_role(user, cleaned["role"])

    logger.info(
        "User created",
        extra={
            "operation": "create_user",
            "user_id": str(user.id),
            "username": user.username,
            "role": cleaned["role"],
            "is_active": user.is_active,
        },
    )

    return user


@transaction.atomic
def update_user(user: User, payload: dict, partial: bool) -> User:
    cleaned = normalize_payload(payload, partial=partial)

    username = cleaned["username"] if cleaned["username"] is not None else user.username
    email = cleaned["email"] if cleaned["email"] is not None else user.email
    ensure_unique(username, email, excluded_user_id=user.id)

    user.username = username
    user.email = email
    user.first_name = (
        cleaned["first_name"] if "first_name" in payload else user.first_name
    )
    user.last_name = cleaned["last_name"] if "last_name" in payload else user.last_name
    if cleaned["is_active"] is not None:
        user.is_active = cleaned["is_active"]
    if cleaned["password"]:
        user.set_password(cleaned["password"])
    user.save()

    if cleaned["role"] is not None:
        assign_role(user, cleaned["role"])

    logger.info(
        "User updated",
        extra={
            "operation": "update_user",
            "user_id": str(user.id),
            "username": user.username,
            "role": resolve_role(user),
            "is_active": user.is_active,
        },
    )

    return user

