import requests
from django.http import HttpResponse, JsonResponse
import json
from django.conf import settings

class RequestRouterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # Map service names to URLs
        self.routes = {
            'account': settings.SERVICES['account'].rstrip('/'),
            'course': settings.SERVICES['course'].rstrip('/'),
        }

        # Map URL paths to services
        self.path_mapping = {
            '/api/signup': 'account',
            '/api/login': 'account',
            '/api/delete': 'account',
            '/api/decode-token': 'account',
            '/api/check-student': 'account',
            '/api/check-user': 'account',
            '/api/me': 'account',

            '/api/courses': 'course',
            '/api/courses/': 'course',
            '/api/delete-student-courses/<uuid>/': 'course',
        }

    def __call__(self, request):
        # Determine which service this request is for
        service_name = None
        for path_prefix, service in self.path_mapping.items():
            if request.path.startswith(path_prefix):
                service_name = service
                break

        if not service_name:
            return self.get_response(request)

        service_url = self.routes[service_name]
        target_url = f"{service_url}{request.path}"

        # Base headers for all requests
        headers = {
            'ngrok-skip-browser-warning': 'true',
            'X-GATEWAY-SECRET': 'AwZKQwAg5nowgvSvSdb4dfPZSC6eM9F_7XH6gokrJEtB93jXEsTJTmYKQGR7xUNn0ns'
        }

        # Forward authorization if exists
        if 'HTTP_AUTHORIZATION' in request.META:
            headers['Authorization'] = request.META['HTTP_AUTHORIZATION']

        # Forward user info from JWT middleware
        user_id = getattr(request, 'user_id', None)
        if user_id:
            headers['X-User-ID'] = user_id

            # Always try to fetch student_id from Account service
            try:
                resp = requests.get(
                    f"{self.routes['account']}/api/check-user/{user_id}/",
                    headers={'X-GATEWAY-SECRET': headers['X-GATEWAY-SECRET']},
                    timeout=5
                )
                if resp.status_code == 200:
                    student_id = resp.json().get('student_id')
                    if student_id:
                        request.student_id = student_id
                        headers['X-Student-ID'] = student_id
                else:
                    print("Account service returned non-200 status:", resp.status_code)
            except Exception as e:
                print("Failed to fetch student_id:", e)

        # Forward username if exists
        username = getattr(request, 'username', None)
        if username:
            headers['X-Username'] = username

        # Detect content type and forward request accordingly
        content_type = request.META.get('CONTENT_TYPE', '')

        try:
            if content_type.startswith('application/json') and request.body:
                try:
                    json_data = json.loads(request.body)
                    response = requests.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        json=json_data,
                        params=request.GET,
                        timeout=10,
                        verify=True
                    )
                except json.JSONDecodeError:
                    response = requests.request(
                        method=request.method,
                        url=target_url,
                        headers=headers,
                        data=request.body,
                        params=request.GET,
                        timeout=10,
                        verify=True
                    )

            elif content_type.startswith('multipart/form-data'):
                # Forward file uploads
                response = requests.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=request.POST,
                    files=request.FILES,
                    params=request.GET,
                    timeout=10,
                    verify=True
                )

            else:
                # Other types (form-urlencoded, text/plain, etc.)
                response = requests.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=request.body,
                    params=request.GET,
                    timeout=10,
                    verify=True
                )

            return HttpResponse(
                content=response.content,
                status=response.status_code,
                content_type=response.headers.get('Content-Type', 'application/json')
            )

        except requests.exceptions.ConnectionError:
            return JsonResponse({'error': 'Cannot connect to service'}, status=503)
        except requests.exceptions.SSLError as e:
            return JsonResponse({'error': f'SSL error: {str(e)}'}, status=502)
        except Exception as e:
            return JsonResponse({'error': f'Gateway error: {str(e)}'}, status=500)
