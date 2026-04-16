from rest_framework.permissions import BasePermission


class IsAdminGroupMember(BasePermission):
    """
    Grants access to users who are staff OR belong to the 'AdminUser' group.
    """
    message = 'Admin access required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return request.user.groups.filter(name='AdminUser').exists()
