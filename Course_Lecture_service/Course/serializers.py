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

class LectureSerializer(serializers.ModelSerializer):
    """
    Serializer for READING lectures (display)
    """
    class Meta:
        model = Lecture
        fields = ['lecture_id', 'student_id', 'course_id', 'lecture_name', 'created_at']
        read_only_fields = ['lecture_id', 'student_id', 'course_id', 'created_at']

class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for courses with their lectures
    """
    lectures = LectureSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = ['course_id', 'course_name', 'course_teacher', 'lectures', 'created_at']
        read_only_fields = ['course_id', 'created_at']