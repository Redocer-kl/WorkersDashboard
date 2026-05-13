from rest_framework import permissions, exceptions


class HasResourcePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise exceptions.NotAuthenticated()

        if request.user.is_superuser:
            return True

        resource_slug = getattr(view, 'resource_slug', None)

        method_actions = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }

        action_slug = method_actions.get(request.method)

        if not resource_slug or not action_slug:
            return False

        return request.user.has_resource_permission(
            resource_slug,
            action_slug
        )


class IsAdminUserRole(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return bool(
            user.role and user.role.slug == 'admin'
        )