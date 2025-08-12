import os

from django.db import models

# Create your models here.
class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    credits = models.IntegerField()
    instructor = models.ForeignKey("users.Professor", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} {self.instructor}"

class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey("users.Student", on_delete=models.CASCADE, related_name="enrollments")
    enroll_date = models.DateField()
    grade = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "student"], name="uniq_course_student_enrollment")
        ]

    def __str__(self):
        return f"{self.course} {self.student} {self.grade}"

def course_material_path(instance, filename):
    return os.path.join('course_materials', str(instance.course.id), filename,)

class CourseMaterial(models.Model):
    PDF = 'pdf'
    VIDEO = 'video'
    LINK = 'link'
    SLIDES = 'slides'

    MATERIAL_TYPE_CHOICES = [
        (PDF, 'PDF'),
        (LINK, 'Link'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES)
    url = models.TextField(blank=True, null=True, default="")
    upload = models.FileField(
        upload_to=course_material_path,
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.material_type})"

class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=255)
    message = models.TextField()
    announcement_date = models.DateField()

    def __str__(self):
        return f"{self.title} ({self.announcement_date})"