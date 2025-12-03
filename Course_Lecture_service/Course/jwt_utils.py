from rest_framework import exceptions
import jwt
from django.conf import settings

def decode_jwt(token):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

def get_student_id_from_token(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise exceptions.AuthenticationFailed('Invalid token header')
    
    token = parts[1]
    
    try:
        payload = decode_jwt(token)
        student_id = payload.get('sub')
        return student_id
    except jwt.PyJWTError:
        raise exceptions.AuthenticationFailed('Invalid token')