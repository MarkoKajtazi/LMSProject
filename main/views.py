import json

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from courses.models import Course, CourseMaterial, Announcement, Enrollment
from exams.models import Exam
from users.models import Professor, TeachingAssistant, Student


# Create your views here.
def home(request):
    user = request.user
    courses = Course.objects.none()

    is_prof = is_student = is_ta = False
    exams_by_date = {}

    if user.is_authenticated:
        is_prof = Professor.objects.filter(user=user).exists()
        is_student = Student.objects.filter(user=user).exists()
        is_ta = TeachingAssistant.objects.filter(user=user).exists()

        courses = (Course.objects
                   .filter(
                       Q(instructor__user=user) |
                       Q(teaching_assistants__user=user) |
                       Q(enrollment__student__user=user)
                   )
                   .distinct()
                   .order_by("name"))

        exams_qs = Exam.objects.filter(
            Q(course__instructor__user=user) |
            Q(registrations__student__user=user)
        ).distinct().order_by("title")

        # (optional) only show exams from user's courses:
        # if courses.exists():
        #     exams_qs = exams_qs.filter(course__in=courses)

        for e in exams_qs:
            # If you care about local timezone crossing midnight, use:
            # exam_date = timezone.localtime(e.exam_date).date()
            exam_date = e.exam_date.date()
            key = exam_date.isoformat()  # 'YYYY-MM-DD'
            exams_by_date.setdefault(key, []).append({
                "id": e.id,
                "title": e.title,
                "course": str(e.course),
                "course_id": e.course_id,
                "course_url": reverse("course", args=[e.course_id]),
                "time": e.exam_date.strftime("%H:%M"),
            })



    context = {
        "courses": courses,
        "is_prof": is_prof,
        "is_student": is_student,
        "is_ta": is_ta,
        "exams_json": json.dumps(exams_by_date),
    }
    return render(request, "home.html", context)


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