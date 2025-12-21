from django.db import models  # pyright: ignore[reportMissingImports]
import uuid

class Course(models.Model):
    course_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student_id = models.UUIDField()  # References Student.student_id from Account service
    course_name = models.CharField(max_length=200)
    course_teacher = models.CharField(max_length=100, blank=True, null=True)  # Optional
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course_name} (Student: {self.student_id})"
    
    class Meta:
        db_table = 'Course'

class Lecture(models.Model):
    SUMMARY_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('READY', 'Ready'),
        ('FAILED', 'Failed'),
    ]

    lecture_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student_id = models.UUIDField()
    course_id = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lectures'
    )
    lecture_name = models.CharField(max_length=200)
    file_name = models.CharField(max_length=255, blank=True, null=True)

    summary_status = models.CharField(
        max_length=20,
        choices=SUMMARY_STATUS_CHOICES,
        default='PENDING'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.lecture_name
    
    class Meta:
        db_table = 'Lecture'