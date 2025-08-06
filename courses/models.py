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
    student = models.ForeignKey("users.Student", on_delete=models.CASCADE)
    enroll_date = models.DateField()
    grade = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.course} {self.student} {self.grade}"

class CourseMaterial(models.Model):
    PDF = 'pdf'
    VIDEO = 'video'
    LINK = 'link'
    SLIDES = 'slides'

    MATERIAL_TYPE_CHOICES = [
        (PDF, 'PDF'),
        (VIDEO, 'Video'),
        (LINK, 'Link'),
        (SLIDES, 'Slides'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES)
    url_or_path = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.material_type})"

class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=255)
    message = models.TextField()
    post_date = models.DateField()

    def __str__(self):
        return f"{self.title} ({self.post_date})"