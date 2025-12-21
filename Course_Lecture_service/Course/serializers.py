from rest_framework import serializers
from .models import Course, Lecture


class LectureCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for CREATING lectures (upload)
    """
    class Meta:
        model = Lecture
        fields = ['lecture_name']  # Only what user provides during upload
    
    def validate_lecture_name(self, value):
        if len(value) > 200:
            raise serializers.ValidationError("Lecture name cannot exceed 200 characters.")
        return value

# serializers.py
class LectureSerializer(serializers.ModelSerializer):
    """
    Serializer for READING lectures (display)
    """
    course_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Lecture
        fields = [
            'lecture_id',
            'student_id',
            'course_id',
            'lecture_name',
            'summary_status',
            'course_info',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['lecture_id', 'student_id', 'course_id', 'created_at', 'updated_at']
    
    def get_course_info(self, obj):
        """Get minimal course info"""
        return {
            'course_id': str(obj.course_id.course_id),
            'course_name': obj.course_id.course_name
        }

# serializers.py
class CourseSerializer(serializers.ModelSerializer):
    lectures = serializers.SerializerMethodField()
    lecture_count = serializers.SerializerMethodField()  # Add this
    
    class Meta: 
        model = Course
        fields = ['course_id', 'course_name', 'course_teacher', 'lectures', 'lecture_count', 'created_at']
    
    def get_lectures(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'student_id'):
            student_id = request.student_id
            lectures = Lecture.objects.filter(course_id=obj, student_id=student_id)
            # Return minimal lecture data for course list
            return [
                {
                    'lecture_id': str(lecture.lecture_id),
                    'lecture_name': lecture.lecture_name,
                    'has_file': bool(lecture.file_name),
                    'created_at': lecture.created_at
                }
                for lecture in lectures[:3]  # Only show first 3 in course list
            ]
        return []
    
    def get_lecture_count(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'student_id'):
            student_id = request.student_id
            return Lecture.objects.filter(course_id=obj, student_id=student_id).count()
        return 0
    
    def get_lectures(self, obj):
        # Get current student from request context
        request = self.context.get('request')
        if request and hasattr(request, 'student_id'):
            student_id = request.student_id
            lectures = Lecture.objects.filter(course_id=obj, student_id=student_id)
            return LectureSerializer(lectures, many=True).data
        return []