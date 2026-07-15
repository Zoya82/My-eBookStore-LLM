from rest_framework.permissions import BasePermission


class IsStaffOrSuperuser(BasePermission):
    message = '仅管理员可以执行此操作'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
