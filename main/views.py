from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404

from courses.models import Course, CourseMaterial, Announcement, Enrollment
from users.models import Professor, TeachingAssistant, Student


# Create your views here.
def home(request):
    user = request.user
    courses = Course.objects.none()

    if user.is_authenticated:
        courses = Course.objects.filter(
            Q(instructor__user=user) |
            Q(teaching_assistants__user=user) |
            Q(enrollment__student__user=user)
        ).distinct().order_by("name")

    context = {"courses": courses}
    return render(request, "home.html", context=context)

def course(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_prof = Course.objects.filter(pk=course_id, instructor__user=user).exists()
    is_ta = Course.objects.filter(pk=course_id, teaching_assistants__user=user).exists()
    is_student = Enrollment.objects.filter(course_id=course_id, student__user=user).exists()

    if not (is_prof | is_ta | is_student):
        return HttpResponseForbidden("You do not have access to this course.")

    courses = Course.objects.filter(
        Q(instructor__user=user) |
        Q(teaching_assistants__user=user) |
        Q(enrollment__student__user=user)
    ).distinct().order_by("name")

    context = {
        "course": course,
        "courses": courses,
        "materials": CourseMaterial.objects.filter(course_id=course_id),
        "announcements": Announcement.objects.filter(course_id=course_id).order_by("announcement_date"),
    }
    return render(request, "course.html", context)