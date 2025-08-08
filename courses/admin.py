from django.contrib import admin
from courses.models import Course, CourseMaterial, Enrollment, Announcement

# Register your models here.
class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0

class AnnouncementInline(admin.TabularInline):
    model = Announcement
    extra = 0

class CourseMaterialInline(admin.TabularInline):
    model = CourseMaterial
    extra = 0
    fields = ('title', 'material_type', 'url', 'upload', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "credits", "instructor")
    search_fields = ("name",)
    list_filter = ("name", "instructor",)
    inlines = [EnrollmentInline, AnnouncementInline, CourseMaterialInline]
