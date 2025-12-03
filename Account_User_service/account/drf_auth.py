from rest_framework import authentication, exceptions
from rest_framework.request import Request
import jwt
from .auth import decode_jwt
from .models import User

class JWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request: Request):
        auth = authentication.get_authorization_header(request).split()
        if not auth:
            raise exceptions.AuthenticationFailed("Unauthorized.")
        if len(auth) != 2 or auth[0].decode().lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed("Unauthorized.")
        token = auth[1].decode()
        try:
            payload = decode_jwt(token)
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed("Unauthorized.")
        user_id = payload.get("sub")
        user = User.objects(id=user_id).first()
        if not user:
            raise exceptions.AuthenticationFailed("Unauthorized.")
        return (user, token)
