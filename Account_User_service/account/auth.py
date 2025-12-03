import jwt # pyright: ignore[reportMissingImports]
from datetime import datetime, timedelta, timezone
from django.conf import settings # pyright: ignore[reportMissingImports]
from .models import User # pyright: ignore[reportMissingImports]

def create_jwt_for_user(user):
    payload = {
        "sub": str(user.user_id),  # Using user_id as subject
        "username": user.username,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.JWT_EXP_DELTA_SECONDS),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

def decode_jwt(token):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])