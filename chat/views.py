# chat/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from courses.models import Course, Enrollment
from .models import ChatRoom
from .acl import user_can_access_course_room

@login_required
def course_chat(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_prof = Course.objects.filter(instructor__user=user).exists()
    is_ta = Course.objects.filter(teaching_assistants__user=user).exists()
    is_student = Enrollment.objects.filter(student__user=user).exists()

    if not (is_prof | is_ta | is_student):
        return HttpResponseForbidden("You do not have access to this course.")

    # Build list of courses the user is involved in (any role)
    courses = Course.objects.filter(
        Q(instructor__user=user) |
        Q(teaching_assistants__user=user) |  # or Q(teaching_assistants=user) if M2M to User
        Q(enrollment__student__user=user)
    ).distinct().order_by("name")

    # Use request.user here
    if not user_can_access_course_room(user, course):
        return HttpResponseForbidden("Not allowed.")

    room, _ = ChatRoom.objects.get_or_create(course=course)
    messages = room.messages.select_related("sender").order_by("-created_at")[:50]
    messages = list(messages)[::-1]
    context = {
        "course": course,
        "messages": messages,
        "courses": courses,
    }
    return render(request, "forum.html", context=context)
