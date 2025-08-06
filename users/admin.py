from django.contrib import admin
from users.models import Student, Professor, TeachingAssistant

# Register your models here.
@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "date_joined")
    exclude = ("role", "user")

@admin.register(TeachingAssistant)
class TAAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "date_joined")
    exclude = ("role", "user")

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "index", "date_joined")
    exclude = ("role", "user", "index")

