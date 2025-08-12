from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from courses.forms import CourseFormForProfessor, CourseForm, EnrollmentForm, EnrollmentPickCourseForm
from courses.models import Course, Enrollment


# Create your views here.
@login_required
def course_create(request):
    is_professor = hasattr(request.user, "professor")

    if not is_professor:
        return HttpResponseForbidden("Only professor can create courses.")

    if request.method == "POST":
        form = CourseFormForProfessor(request.POST) if is_professor else CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            if is_professor:
                course.instructor = request.user.professor
            course.save()
            messages.success(request, "Course created successfully.")
            # adjust the redirect to your route; in your project it looked like name='course'
            return redirect("course", course_id=course.id)
    else:
        form = CourseFormForProfessor() if is_professor else CourseForm()

    return render(request, "courses/course_form.html", {"form": form})

@login_required
def enroll_choose_course(request):
    if not hasattr(request.user, "student"):
        return HttpResponseForbidden("Only students can enroll in courses.")

    student = request.user.student

    if request.method == "POST":
        form = EnrollmentPickCourseForm(request.POST, student=student)
        if form.is_valid():
            course = form.cleaned_data["course"]
            enroll_date = timezone.now().date()
            # prevent double-enroll (works best if you added a UniqueConstraint)
            obj, created = Enrollment.objects.get_or_create(
                student=student, course=course, enroll_date=enroll_date,
            )
            if created:
                messages.success(request, f"Enrolled in {course.name}.")
            else:
                messages.info(request, f"You are already enrolled in {course.name}.")
            return redirect("course", course_id=course.id)
    else:
        form = EnrollmentPickCourseForm(student=student)

    return render(request, "courses/enroll_form.html", {"form": form})