# course_service/jwt_utils.py
from rest_framework import exceptions
import jwt
from django.conf import settings
import requests

def decode_jwt(token):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

def get_student_id_from_token(request):
    """
    Get student_id from token AND verify user exists in account service
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise exceptions.AuthenticationFailed('Invalid token header')
    
    token = parts[1]
    
    try:
        # 1. Decode token - the 'sub' field contains USER ID, not student_id!
        payload = decode_jwt(token)
        user_id = payload.get('sub')  # RENAME: This is USER ID!
        
        if not user_id:
            raise exceptions.AuthenticationFailed('No user ID in token')
        
        print(f"DEBUG: Extracted user_id = {user_id}")
        
        # 2. Check if user exists in account service (using user_id)
        try:
            response = requests.get(
                f'http://localhost:8000/api/check-user/{user_id}/',  # Using user_id
                timeout=2
            )
            
            print(f"DEBUG: Account service response status = {response.status_code}")
            
            if response.status_code == 404:
                raise exceptions.AuthenticationFailed('Account has been deleted. Please login again.')
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('exists', False):
                    raise exceptions.AuthenticationFailed('User account no longer exists')
                
                # Get the actual student_id from response
                student_id = data.get('student_id')
                print(f"DEBUG: Got student_id from response = {student_id}")
                return student_id  # Return the REAL student_id
                
        except requests.exceptions.Timeout:
            print("Warning: Account service timeout during token validation")
            # Can't verify, so we can't return a student_id
            return None
            
        except requests.exceptions.ConnectionError:
            print("Warning: Cannot connect to account service")
            return None
        
        # If we get here without returning, something went wrong
        return None
        
    except jwt.ExpiredSignatureError:
        raise exceptions.AuthenticationFailed('Token expired')
    except jwt.PyJWTError as e:
        raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
    except Exception as e:
        raise exceptions.AuthenticationFailed(f'Authentication error: {str(e)}')