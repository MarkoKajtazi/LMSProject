from datetime import datetime

from django.db import models


# Create your models here.
class Exam(models.Model):
    EXAM_CHOICES = {
        ("mi", "midterm"),
        ("fi", "final"),
        ("or", "oral"),
        ("qu", "quiz"),
        ("ma", "makeup"),
    }
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    exam_type = models.CharField(max_length=2, choices=EXAM_CHOICES)
    exam_date = models.DateTimeField()
    max_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.course} {self.title}"


class ExamRegistration(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="registrations")
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    registration_date = models.DateTimeField(blank=True, default=datetime.now)
    attended = models.BooleanField(default=False)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.exam} {self.student}"


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    max_score = models.IntegerField(default=0)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.question} {self.order}"


class StudentAnswer(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE, related_name="answers")
    answer = models.TextField()
    answer_date = models.DateTimeField(blank=True, default=datetime.now)
    scored = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student}: {self.answer}"

    class Meta:
        unique_together = ("question", "student")

    def save(self, *args, **kwargs):
        if self.exam_id is None and self.question_id:
            self.exam_id = self.question.exam_id
        super().save(*args, **kwargs)