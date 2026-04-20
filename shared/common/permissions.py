from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            getattr(request.user, "is_authenticated", False)
            and getattr(request.user, "user_type", None) == "staff"
        )


class IsCustomerUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            getattr(request.user, "is_authenticated", False)
            and getattr(request.user, "user_type", None) == "customer"
        )


class IsInternalService(BasePermission):
    def has_permission(self, request, view):
        return bool(
            getattr(request.user, "is_authenticated", False)
            and getattr(request.user, "user_type", None) == "service"
        )
