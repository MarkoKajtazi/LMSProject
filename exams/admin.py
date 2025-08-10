from django.contrib import admin

from exams.models import Exam, ExamRegistration, ExamQuestion, StudentAnswer

# Register your models here.
class ExamRegistrationInline(admin.TabularInline):
    model = ExamRegistration
    extra = 0

class ExamQuestionInline(admin.TabularInline):
    model = ExamQuestion
    extra = 0

class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    exclude = ("answer_date",)

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "exam_type", "exam_date")
    inlines = [ExamRegistrationInline, ExamQuestionInline, StudentAnswerInline]