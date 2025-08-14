from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404

from courses.models import Course, CourseMaterial, Announcement, Enrollment
from exams.models import Exam
from users.models import Professor, TeachingAssistant, Student


# Create your views here.
def home(request):
    user = request.user
    courses = Course.objects.none()

    is_prof = False
    is_student = False
    is_ta = False

    if request.user.is_authenticated:
        is_prof = Professor.objects.filter(user=request.user).exists()
        is_student = Student.objects.filter(user=request.user).exists()
        is_ta = TeachingAssistant.objects.filter(user=request.user).exists()

    if user.is_authenticated:
        courses = Course.objects.filter(
            Q(instructor__user=user) |
            Q(teaching_assistants__user=user) |
            Q(enrollment__student__user=user)
        ).distinct().order_by("name")

    context = {
        "courses": courses,
        "is_prof": is_prof,
        "is_student": is_student,
        "is_ta": is_ta,
    }
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

    exams = Exam.objects.filter(
        Q(course_id__exact=course_id),
        Q(course__instructor__user=user) |
        Q(registrations__student__user=user)
    ).distinct().order_by("title")

    context = {
        "course": course,
        "courses": courses,
        "exams": exams,
        "materials": CourseMaterial.objects.filter(course_id=course_id),
        "announcements": Announcement.objects.filter(course_id=course_id).order_by("announcement_date"),
        "is_prof": Professor.objects.filter(user=user).exists(),
        "is_student": Student.objects.filter(user=user).exists(),
        "is_ta": TeachingAssistant.objects.filter(user=user).exists(),
    }
    return render(request, "courses/course.html", context)