from django.db import DatabaseError, connection
from django.http import JsonResponse


def health(request):  # noqa: ARG001
    return JsonResponse({"status": "ok"})


def ready(request):  # noqa: ARG001
    try:
        connection.ensure_connection()
    except DatabaseError:
        return JsonResponse({"status": "not_ready"}, status=503)
    return JsonResponse({"status": "ready"})
