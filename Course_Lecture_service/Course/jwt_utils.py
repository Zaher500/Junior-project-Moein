# jwt_utils.py
from rest_framework import exceptions
import requests

def get_student_id_from_token(request):
    """
    Get student_id from request headers (sent by gateway)
    """
    # Django stores headers as HTTP_X_STUDENT_ID in META
    student_id = request.META.get('HTTP_X_STUDENT_ID')
    
    if student_id:
        return student_id
    
    # Also check direct headers attribute (for DRF)
    student_id = request.headers.get('X-Student-ID')
    if student_id:
        return student_id
    
    # Check if gateway set it as request attribute
    if hasattr(request, 'student_id'):
        return request.student_id
    
    # Fallback: check for X-User-ID
    user_id = request.META.get('HTTP_X_USER_ID') or request.headers.get('X-User-ID')
    
    if user_id:
        try:
            
            response = requests.get(
                f'https://marielle-subchondral-rex.ngrok-free.dev/api/check-user/{user_id}/',
                headers={
                    'X-GATEWAY-SECRET': 'AwZKQwAg5nowgvSvSdb4dfPZSC6eM9F_7XH6gokrJEtB93jXEsTJTmYKQGR7xUNn0ns'
                },
                timeout=10
            )
            if response.status_code == 200:
                student_id = response.json().get('student_id')
                if student_id:
                    return student_id
        except Exception as e:
            print(f"Failed to fetch student_id from account service: {e}")
    
    # No student_id found
    return None