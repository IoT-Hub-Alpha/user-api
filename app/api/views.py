import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from iot_auth.django import CheckPermissionsMixin

from app.services.user_service import (
    ApiError,
    assign_role,
    create_user,
    get_user_or_404,
    list_roles,
    paginated_users,
    parse_json_body,
    resolve_role,
    serialize_user,
    update_user,
)


logger = logging.getLogger(__name__)


def handle_api_error(exc: ApiError) -> JsonResponse:
    return JsonResponse({"detail": exc.detail}, status=exc.status_code)


@method_decorator(csrf_exempt, name="dispatch")
class UserListView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["users.view"],
        "post": ["users.add"],
    }

    def get(self, request: HttpRequest) -> JsonResponse:
        try:
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 10))
            payload = paginated_users(page=page, page_size=page_size)
        except ValueError:
            return JsonResponse(
                {"detail": "Pagination values must be integers."},
                status=400,
            )
        except ApiError as exc:
            return handle_api_error(exc)
        return JsonResponse(payload, status=200)

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            user = create_user(parse_json_body(request))
        except ApiError as exc:
            return handle_api_error(exc)
        return JsonResponse({"data": serialize_user(user)}, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class UserDetailView(CheckPermissionsMixin, View):
    permission_map = {
        "get": ["users.view"],
        "put": ["users.change"],
        "patch": ["users.change"],
        "delete": ["users.delete"],
    }

    def get(self, request: HttpRequest, user_id: int) -> JsonResponse:
        try:
            user = get_user_or_404(user_id)
        except ApiError as exc:
            return handle_api_error(exc)
        return JsonResponse({"data": serialize_user(user)}, status=200)

    def put(self, request: HttpRequest, user_id: int) -> JsonResponse:
        return self._update(request, user_id, partial=False)

    def patch(self, request: HttpRequest, user_id: int) -> JsonResponse:
        return self._update(request, user_id, partial=True)

    def delete(self, request: HttpRequest, user_id: int) -> HttpResponse:
        try:
            user = get_user_or_404(user_id)
        except ApiError as exc:
            return handle_api_error(exc)
        user_log_data = {
            "operation": "delete_user",
            "user_id": str(user.id),
            "username": user.username,
            "role": resolve_role(user),
            "is_active": user.is_active,
        }
        user.delete()
        logger.info("User deleted", extra=user_log_data)
        return HttpResponse(status=204)

    def _update(
        self, request: HttpRequest, user_id: int, partial: bool
    ) -> JsonResponse:
        try:
            user = get_user_or_404(user_id)
            updated = update_user(user, parse_json_body(request), partial=partial)
        except ApiError as exc:
            return handle_api_error(exc)
        return JsonResponse({"data": serialize_user(updated)}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class UserRoleView(CheckPermissionsMixin, View):
    permission_map = {
        "put": ["users.change_role"],
    }

    def put(self, request: HttpRequest, user_id: int) -> JsonResponse:
        try:
            user = get_user_or_404(user_id)
            payload = parse_json_body(request)
            updated = assign_role(user, payload.get("role", ""))
        except ApiError as exc:
            return handle_api_error(exc)
        return JsonResponse({"data": serialize_user(updated)}, status=200)


class RoleListView(CheckPermissionsMixin, View):
    required_permissions = ["roles.view"]

    def get(self, request: HttpRequest) -> JsonResponse:  # noqa: ARG002
        return JsonResponse({"data": list_roles()}, status=200)
