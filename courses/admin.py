from django.contrib import admin
from courses.models import Course, CourseMaterial, Enrollment, Announcement


# Register your models here.
class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0

class AnnouncementInline(admin.TabularInline):
    model = Announcement
    extra = 0

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "credits", "instructor")
    search_fields = ("name",)
    list_filter = ("name", "instructor",)
    inlines = [EnrollmentInline, AnnouncementInline]

@admin.register(CourseMaterial)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "material_type", "uploaded_at")