from django.db import models

# Create your models here.
class Assignment(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    due_date = models.DateTimeField()
    max_points = models.IntegerField()

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    content = models.TextField()
    score = models.IntegerField(null=True, blank=True)
