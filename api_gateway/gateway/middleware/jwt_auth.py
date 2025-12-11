import jwt
from django.http import JsonResponse

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip auth for ALL public endpoints
        public_paths = [
            '/api/signup/',
            '/api/login/',
            '/health/',
            '/api/decode-token/',
            '/api/check-student/',  # Course service calls this
            '/api/check-user/',     # Account service needs this
        ]
        
        # Check if path starts with any public path
        for path in public_paths:
            if request.path.startswith(path):
                return self.get_response(request)
        
        # Check for Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            return JsonResponse({'error': 'No authorization header'}, status=401)
        
        # Validate Bearer token format
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return JsonResponse({'error': 'Invalid token format'}, status=401)
        
        token = parts[1]
        
        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token, 
                'AwZKQwAg5nowgvSvSdb4dfPZSC6eM9F_7XH6gokrJEtB93jXEsTJTmYKQGR7xUNn0ns',
                algorithms=['HS256']
            )
            
            # Add user info to request
            request.user_id = payload.get('sub')
            request.username = payload.get('username')
            
            return self.get_response(request)
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)