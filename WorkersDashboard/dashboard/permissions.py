from rest_framework import permissions

class HasResourcePermission(permissions.BasePermission):
    """
    Кастомный класс разрешений для проверки доступа через RBAC.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        resource_slug = getattr(view, 'resource_slug', None)
        
        method_actions = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        action_slug = method_actions.get(request.method)

        if not resource_slug or not action_slug:
            return False
            
        return request.user.has_resource_permission(resource_slug, action_slug)