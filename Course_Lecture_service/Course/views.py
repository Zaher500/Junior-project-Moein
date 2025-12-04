# ==============================================================================
# STANDARD LIBRARY IMPORTS
# ==============================================================================
import os
import uuid

# ==============================================================================
# DJANGO IMPORTS
# ==============================================================================
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# ==============================================================================
# DRF (Django REST Framework) IMPORTS
# ==============================================================================
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# ==============================================================================
# LOCAL APPLICATION IMPORTS
# ==============================================================================
from .models import Course, Lecture
from .serializers import (
    CourseSerializer,
    LectureCreateSerializer,
    LectureSerializer
)
from .jwt_utils import get_student_id_from_token


# ==============================================================================
# VIEW FUNCTIONS
# ==============================================================================
@api_view(['POST'])
def create_course(request):
    """
    Create a new course for the authenticated student
    Body: {"course_name": "Mathematics", "course_teacher": "Dr. Smith"}
    """
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    serializer = CourseSerializer(data=request.data)
    if serializer.is_valid():
        # Create course with the authenticated student_id
        course = Course.objects.create(
            student_id=student_id,
            course_name=serializer.validated_data['course_name'],
            course_teacher=serializer.validated_data.get('course_teacher', '')
        )
        return Response(CourseSerializer(course).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# READ - Get all courses for student
@api_view(['GET'])
def get_my_courses(request):
    """
    Get all courses for the authenticated student
    """
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    courses = Course.objects.filter(student_id=student_id)
    serializer = CourseSerializer(courses, many=True)
    return Response({
        'count': courses.count(),
        'courses': serializer.data
    })

# READ - Get specific course
@api_view(['GET'])
def get_course(request, course_id):
    """
    Get a specific course (only if owned by student)
    """
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        course = Course.objects.get(course_id=course_id, student_id=student_id)
        serializer = CourseSerializer(course)
        return Response(serializer.data)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_course_lectures(request, course_id):
    """
    Get all lectures for a specific course WITH FILE URLS
    URL: GET /api/courses/COURSE_ID/lectures/
    """
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        course = Course.objects.get(course_id=course_id, student_id=student_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=404)
    
    lectures = Lecture.objects.filter(course_id=course_id, student_id=student_id)
    
    # Get all files in the folder
    folder_path = os.path.join(settings.MEDIA_ROOT, str(student_id), str(course_id))

    print("=" * 50)
    print(f"DEBUG - Looking for files in: {folder_path}")
    print(f"DEBUG - Folder exists: {os.path.exists(folder_path)}")
    
    if os.path.exists(folder_path):
        print(f"DEBUG - Files in folder: {os.listdir(folder_path)}")
    else:
        print(f"DEBUG - Folder doesn't exist!")
    
    # Check parent directory
    parent_path = os.path.join(settings.MEDIA_ROOT, str(student_id))
    print(f"DEBUG - Parent folder ({parent_path}) exists: {os.path.exists(parent_path)}")
    if os.path.exists(parent_path):
        print(f"DEBUG - Contents of parent folder: {os.listdir(parent_path)}")
    
    print("=" * 50)

    all_files = os.listdir(folder_path) if os.path.exists(folder_path) else []
    
    lectures_data = []
    for lecture in lectures:
        lecture_dict = LectureSerializer(lecture).data
        
        # =============================================
        # UPDATED LOGIC: Use the stored file_name field
        # =============================================
        if lecture.file_name:  # Check if lecture has a stored filename
            # Check if the file actually exists in the folder
            if lecture.file_name in all_files:
                filename = lecture.file_name
                # Create the URL
                file_url = f"{request.scheme}://{request.get_host()}/media/lectures/{student_id}/{course_id}/{filename}"
                
                lecture_dict['file_url'] = file_url
                lecture_dict['filename'] = filename
                lecture_dict['has_file'] = True
            else:
                # File was recorded but doesn't exist in folder
                lecture_dict['file_url'] = None
                lecture_dict['filename'] = None
                lecture_dict['has_file'] = False
        else:
            # No file_name stored for this lecture
            lecture_dict['file_url'] = None
            lecture_dict['filename'] = None
            lecture_dict['has_file'] = False
        # =============================================
        # END OF UPDATED LOGIC
        # =============================================
        
        lectures_data.append(lecture_dict)
    
    return Response({
        'course': CourseSerializer(course).data,
        'lectures': lectures_data,
        'count': lectures.count()
    })


@api_view(['PUT'])
def update_course(request, course_id):
    """
    Update a course (only if owned by student)
    Body: {"course_name": "New Name", "course_teacher": "New Teacher"}
    """
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        course = Course.objects.get(course_id=course_id, student_id=student_id)
        serializer = CourseSerializer(course, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_course(request, course_id):
    """
    Delete a course (only if owned by student) AND ALL ITS FILES
    """
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        course = Course.objects.get(course_id=course_id, student_id=student_id)
        
        # 1. Delete all files and the folder
        course_folder = os.path.join(
            settings.MEDIA_ROOT,
            str(student_id),
            str(course_id)
        )
        
        files_deleted = []
        folder_deleted = False
        
        if os.path.exists(course_folder):
            # Delete all files
            for filename in os.listdir(course_folder):
                file_path = os.path.join(course_folder, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    files_deleted.append(filename)
            
            # Delete the folder
            os.rmdir(course_folder)
            folder_deleted = True
        
        # 2. Delete the course (cascades to lectures)
        course_name = course.course_name
        course.delete()
        
        return Response({
            'message': 'Course and all lectures deleted',
            'deleted_course': course_name,
            'files_deleted': files_deleted,
            'files_count': len(files_deleted),
            'folder_deleted': folder_deleted
        })
        
    except Course.DoesNotExist:
        return Response({'error': 'Course not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

#///////////////////////////////////////////////////////////////////////////////////////////////////////

@api_view(['POST'])
@csrf_exempt
@parser_classes([MultiPartParser, FormParser])
def upload_lecture(request, course_id):
    """
    Upload lecture to a specific course
    URL: POST /api/courses/COURSE_ID/lectures/upload/
    """
    # 1. Authentication
    student_id = get_student_id_from_token(request)

    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # 2. Authorization - check if course belongs to student
    try:
        course = Course.objects.get(course_id=course_id, student_id=student_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    
    # 3. Validate lecture data using serializer
    serializer = LectureCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 4. File validation
    if 'file' not in request.FILES:
        return Response({'error': 'No file submitted'}, status=status.HTTP_400_BAD_REQUEST)
    
    uploaded_file = request.FILES['file']
    
    allowed_types = [
        'application/pdf', 
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ]
    
    allowed_extensions = ['.pdf', '.docx', '.pptx']
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    
    if (uploaded_file.content_type not in allowed_types and 
        file_extension not in allowed_extensions):
        return Response(
            {'error': 'Only PDF, Word, and PowerPoint files are allowed'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 5. Create secure file path
        student_id_str = str(student_id)
        course_id_str = str(course_id)
        
        upload_dir = os.path.join(settings.MEDIA_ROOT, student_id_str, course_id_str)
        os.makedirs(upload_dir, exist_ok=True)
        
        # 6. Generate unique filename
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        

        print(f"DEBUG - MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"DEBUG - upload_dir: {upload_dir}")
        print(f"DEBUG - File saved to: {file_path}")
        
        # 7. Save file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # 8. Get lecture name from validated serializer data
        lecture_name = serializer.validated_data['lecture_name']
        
        # 9. Create lecture record - FIXED: Use the course object directly
        lecture = Lecture.objects.create(
            student_id=student_id,
            course_id=course,  # Pass the Course object directly
            lecture_name=lecture_name,
            file_name=unique_filename,
        )
        
        # 10. Return response
        return Response({
            'message': 'Lecture uploaded successfully',
            'lecture': LectureSerializer(lecture).data,
            'file_saved_as': unique_filename  # Return filename in response
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Upload failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
def update_lecture_name(request, course_id, lecture_id):
    """
    Update lecture name within a specific course
    URL: PUT /api/courses/COURSE_ID/lectures/LECTURE_ID/update-name/
    Body: {"lecture_name": "New Lecture Name"}
    """
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        course = Course.objects.get(course_id=course_id, student_id=student_id)
    except Course.DoesNotExist:
        return Response({'error': 'Course not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        # FIXED: Use course_id (ForeignKey) with the course object or course_id value
        lecture = Lecture.objects.get(
            lecture_id=lecture_id,
            course_id=course_id,  # This works because course_id is the UUID value
            student_id=student_id
        )
    except Lecture.DoesNotExist:
        return Response({'error': 'Lecture not found or access denied'}, status=status.HTTP_404_NOT_FOUND)
    
    new_lecture_name = request.data.get('lecture_name')
    if not new_lecture_name:
        return Response({'error': 'lecture_name field is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_lecture_name == lecture.lecture_name:
        return Response({'error': 'New name is identical to current name'}, status=status.HTTP_400_BAD_REQUEST)
    
    # FIXED: Use course_id with the UUID value
    existing_lecture = Lecture.objects.filter(
        course_id=course_id,  # Use the UUID value
        student_id=student_id,
        lecture_name__iexact=new_lecture_name
    ).exclude(lecture_id=lecture_id)
    
    if existing_lecture.exists():
        return Response({'error': f'Lecture name "{new_lecture_name}" already exists in this course'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        old_name = lecture.lecture_name
        lecture.lecture_name = new_lecture_name
        lecture.save()
        
        serializer = LectureSerializer(lecture)
        return Response({
            'message': 'Lecture name updated successfully',
            'old_name': old_name,
            'new_name': new_lecture_name,
            'lecture': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': f'Failed to update lecture name: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_lecture(request, course_id, lecture_id):
    """
    Delete a lecture from a course and remove the physical file
    URL: DELETE /api/courses/COURSE_ID/lectures/LECTURE_ID/delete/
    """
    # 1. Authentication
    student_id = get_student_id_from_token(request)
    if not student_id:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # 2. Authorization - check if course belongs to student
    try:
        course = Course.objects.get(course_id=course_id, student_id=student_id)
    except Course.DoesNotExist:
        return Response(
            {'error': 'Course not found or access denied'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 3. Get the lecture and verify ownership
    try:
        lecture = Lecture.objects.get(
            lecture_id=lecture_id,
            course_id=course_id,
            student_id=student_id
        )
    except Lecture.DoesNotExist:
        return Response(
            {'error': 'Lecture not found or access denied'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # 4. Delete the physical file using the stored file_name
        file_deleted = False
        folder_deleted = False
        
        if lecture.file_name:  # Check if we have filename stored
            file_path = os.path.join(
                settings.MEDIA_ROOT,
                'lectures',
                str(student_id),
                str(course_id),
                lecture.file_name
            )
            
            if os.path.exists(file_path):
                os.remove(file_path)
                file_deleted = True
                print(f"✅ Deleted file: {file_path}")
                
                # Check if folder is now empty
                folder_path = os.path.join(
                    settings.MEDIA_ROOT,
                    str(student_id),
                    str(course_id)
                )
                
                if os.path.exists(folder_path) and not os.listdir(folder_path):
                    os.rmdir(folder_path)
                    folder_deleted = True
                    print(f"✅ Deleted empty folder: {folder_path}")
            else:
                print(f"⚠️ File not found: {file_path}")
        else:
            print(f"⚠️ Lecture has no file_name stored: {lecture.lecture_id}")
        
        # 5. Delete the lecture record from database
        lecture_name = lecture.lecture_name
        lecture.delete()
        
        return Response({
            'message': 'Lecture deleted successfully',
            'deleted_lecture': lecture_name,
            'course': course.course_name,
            'file_deleted': file_deleted,
            'folder_deleted': folder_deleted,
            'note': 'Folder only deleted if it became empty'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to delete lecture: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_student_courses(request, student_id):
    """Simple endpoint to delete all courses for a student"""
    try:
        from .models import Course
        Course.objects.filter(student_id=student_id).delete()
        
        return Response({
            'message': f'Courses deleted for student {student_id}',
            'deleted': True
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

