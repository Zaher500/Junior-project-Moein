# ==============================================================================
# STANDARD LIBRARY IMPORTS
# ==============================================================================
import requests

# ==============================================================================
# DJANGO & DRF IMPORTS
# ==============================================================================
from rest_framework import status, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

# ==============================================================================
# LOCAL APPLICATION IMPORTS
# ==============================================================================
from .models import User, Student
from .serializers import (
    DeleteAccountSerializer,
    UserLoginSerializer,
    UserSignupSerializer,
    UserSerializer
)
from .auth import create_jwt_for_user
from .jwt_utils import get_user_from_token


# ==============================================================================
# VIEW FUNCTIONS
# ==============================================================================
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
    

@api_view(['DELETE'])
def delete_account(request):
    try:
        user = get_user_from_token(request)
        if not user:
            return Response({'error': 'Authentication required'}, status=401)
        
        password = request.data.get('password')
        if not password or not user.check_password(password):
            return Response({'error': 'Incorrect password'}, status=400)
        
        # Get student ID
        student = Student.objects.get(user_id=user)
        student_id = str(student.student_id)
        username = user.username
        
        # SIMPLE: Try to delete courses (one attempt only)
        try:
            response = requests.delete(
                f"http://localhost:8001/api/delete-student-courses/{student_id}/",
                timeout=3
            )
            courses_deleted = response.status_code == 200
        except:
            courses_deleted = False
        
        # Delete the user
        user.delete()
        
        return Response({
            'message': f'Account {username} deleted',
            'courses_deleted': courses_deleted,
            'deleted': True
        }, status=200)
                
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])  
def decode_token_contents(request):
    """
    Debug: Show what's inside the JWT token (decode without database check)
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header:
        return Response({'error': 'No Authorization header'}, status=400)
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return Response({'error': 'Invalid Authorization format'}, status=400)
    
    token = parts[1]
    
    try:
        import jwt
        # Decode WITHOUT verification to see raw contents
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        return Response({
            'token': token[:50] + '...' if len(token) > 50 else token,
            'token_length': len(token),
            'decoded_payload': decoded,
            'sub_field': decoded.get('sub'),
            'sub_field_type': type(decoded.get('sub')).__name__,
            'sub_field_length': len(str(decoded.get('sub', ''))),
            'all_fields': list(decoded.keys())
        })
    except Exception as e:
        return Response({'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def check_student_exists(request, student_id):

    """
    Check if a student (and their user account) exists
    Using: Student ID → Find Student → Find User
    """
    try:
        # 1. Find the student by student_id
        student = Student.objects.get(student_id=student_id)
        
        # 2. Get the user from the student
        user = student.user_id
        
        return Response({
            'exists': True,
            'user_id': str(user.user_id),
            'student_id': str(student.student_id),
            'username': user.username,
            'is_active': True
        })
        
    except Student.DoesNotExist:
        # Student not found = user account deleted
        return Response({
            'exists': False,
            'message': 'Student account not found'
        }, status=404)   


@api_view(['GET'])
@permission_classes([AllowAny])
def check_user_exists(request, user_id):

    """Check if user exists by user_id"""
    try:
        user = User.objects.get(user_id=user_id)
        
        # Get the student profile
        student = Student.objects.get(user_id=user)
        
        return Response({
            'exists': True,
            'user_id': str(user.user_id),
            'student_id': str(student.student_id),
            'username': user.username,
            'is_active': True
        })
        
    except User.DoesNotExist:
        return Response({'exists': False}, status=404)
    except Student.DoesNotExist:
        return Response({'exists': False}, status=404)

