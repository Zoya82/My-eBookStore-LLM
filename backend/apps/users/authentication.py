from rest_framework import authentication, exceptions
from django.contrib.auth import get_user_model
import jwt
from django.conf import settings

User = get_user_model()

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate_header(self, request):
        return 'Bearer'

    def authenticate(self, request):
        header = request.headers.get('Authorization')
        if not header: return None
        parts = header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise exceptions.AuthenticationFailed('Authorization 格式错误，应为 Bearer <token>')
        try:
            payload = jwt.decode(parts[1], settings.SECRET_KEY, algorithms=['HS256'])
            user = User.objects.get(pk=payload.get('user_id'))
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token 已过期')
        except (jwt.InvalidTokenError, User.DoesNotExist, TypeError, ValueError):
            raise exceptions.AuthenticationFailed('Token 无效或用户不存在')
        if not user.is_active: raise exceptions.AuthenticationFailed('用户已停用')
        return user, parts[1]
