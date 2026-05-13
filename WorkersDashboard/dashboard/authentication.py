from rest_framework import authentication, exceptions
from dashboard.models import User
from .security import decode_access_token

class CustomJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        user_id = decode_access_token(token)

        if user_id is None:
            raise exceptions.AuthenticationFailed('Invalid or expired token')

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found or inactive')

        return (user, None)