from django.contrib import admin

from assignments.models import Assignment, Submission


# Register your models here.
class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'due_date', 'max_points')
    list_filter = ('course', 'due_date')
    inlines = [SubmissionInline]