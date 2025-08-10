from django.db import models

# Create your models here.
class Exam(models.Model):
    EXAM_CHOICES = {
       ( "mi", "midterm"),
       ( "fi", "final"),
       ( "or", "oral"),
       ( "qu", "quiz"),
       ( "ma", "makeup"),
    }
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    exam_type = models.CharField(max_length=2, choices=EXAM_CHOICES)
    exam_date = models.DateTimeField()
    max_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} on {str(self.exam_date)}"

class ExamRegistration(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    registration_date = models.DateTimeField()
    attended = models.BooleanField(default=False)
    score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.exam} {self.student}"

class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.TextField()
    max_score = models.IntegerField(default=0)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.exam}: {self.question}"

class StudentAnswer(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    question = models.ForeignKey(ExamQuestion, on_delete=models.CASCADE)
    answer = models.TextField()
    answer_date = models.DateTimeField()
    scored = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student}: {self.answer}"

