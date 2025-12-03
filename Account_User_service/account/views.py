from rest_framework import status, exceptions  
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User, Student
from .serializers import UserLoginSerializer, UserSignupSerializer, UserSerializer
from .auth import create_jwt_for_user
from .jwt_utils import get_user_from_token

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    """
    User registration endpoint
    Expected JSON:
    {
        "username": "john_doe",
        "email": "john@example.com", 
        "phone": "1234567890",
        "password": "password123",
        "password_confirm": "password123"
    }
    """
    serializer = UserSignupSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save() 
        
        # Get the student profile
        student = Student.objects.get(user_id=user)
        
        return Response({
            'message': 'User created successfully. Please login to continue.',
            'user': {
                'user_id': str(user.user_id),
                'username': user.username,
                'email': user.email,
                'phone': user.phone
            },
            'student': {
                'student_id': str(student.student_id)
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    User login endpoint
    Expected JSON:
    {
        "username": "john_doe",
        "password": "password123"
    }
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT token
        token = create_jwt_for_user(user)
        
        
        # Get student profile
        student = Student.objects.get(user_id=user)
        
        return Response({
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': str(user.user_id),
                'username': user.username,
                'email': user.email,
                'phone': user.phone
            },
            'student': {
                'student_id': str(student.student_id)
            }
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


# @api_view(['GET'])
# def user_profile(request):
#     """
#     Protected endpoint - manually check JWT token
#     """
#     try:
#         user = get_user_from_token(request)
#         if not user:
#             return Response({'error': 'Token required'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         # Get student profile
#         student = Student.objects.get(user_id=user)
        
#         return Response({
#             'message': 'This is a protected endpoint!',
#             'user': {
#                 'user_id': str(user.user_id),
#                 'username': user.username,
#                 'email': user.email,
#                 'phone': user.phone
#             },
#             'student': {
#                 'student_id': str(student.student_id)
#             }
#         }, status=status.HTTP_200_OK)
        
#     except exceptions.AuthenticationFailed as e:
#         return Response({'error': str(e.detail)}, status=status.HTTP_401_UNAUTHORIZED)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# @api_view(['GET'])
# def protected_test(request):
#     """
#     Another protected endpoint
#     """
#     try:
#         user = get_user_from_token(request)
#         if not user:
#             return Response({'error': 'Token required'}, status=status.HTTP_401_UNAUTHORIZED)
        
#         return Response({
#             'message': f'Hello {user.username}!',
#             'user_id': str(user.user_id),
#             'protected': True
#         }, status=status.HTTP_200_OK)
        
#     except exceptions.AuthenticationFailed as e:
#         return Response({'error': str(e.detail)}, status=status.HTTP_401_UNAUTHORIZED)
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)