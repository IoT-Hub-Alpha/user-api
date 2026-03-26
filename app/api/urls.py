from django.urls import path

from .views import RoleListView, UserDetailView, UserListView, UserRoleView


urlpatterns = [
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:user_id>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<int:user_id>/role/", UserRoleView.as_view(), name="user-role"),
    path("roles/", RoleListView.as_view(), name="role-list"),
]
