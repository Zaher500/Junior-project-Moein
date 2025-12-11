from rest_framework import exceptions
import requests

def get_student_id_from_token(request):
    """
    Get student_id directly from gateway header.
    """
    student_id = request.headers.get('X-Student-ID')
    if student_id:
        return student_id

    # Optional fallback: get from X-User-ID by calling Account service
    user_id = request.headers.get('X-User-ID')
    if user_id:
        try:
            response = requests.get(
                f'https://marielle-subchondral-rex.ngrok-free.dev/api/check-user/{user_id}/',
                timeout=2
            )
            if response.status_code == 200:
                student_id = response.json().get('student_id')
                if student_id:
                    return student_id
        except Exception:
            pass

    raise exceptions.AuthenticationFailed('No student_id from gateway')
