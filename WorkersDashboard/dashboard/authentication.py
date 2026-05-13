# authentication.py
from rest_framework import authentication, exceptions
from dashboard.models import User
from .security import decode_access_token

class CustomJWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None 

        token = parts[1]
        user_id = decode_access_token(token)

        if user_id is None:
            raise exceptions.AuthenticationFailed('Invalid or expired token')

        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User not found or inactive')

        return (user, None)

    def authenticate_header(self, request):
        return 'Bearer'