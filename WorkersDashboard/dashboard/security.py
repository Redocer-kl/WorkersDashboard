import jwt
import datetime
from django.conf import settings
from dashboard.models import User

def generate_access_token(user):
    """Создает JWT токен для пользователя."""
    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=2), # Время жизни
        'iat': datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

def decode_access_token(token):
    """Декодирует и проверяет токен."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None