# chat/views.py
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from courses.models import Course
from .models import ChatRoom
from .acl import user_can_access_course_room

@login_required
def course_chat(request, course_id):
    course = get_object_or_404(Course, pk=course_id)

    # Use request.user here
    if not user_can_access_course_room(request.user, course):
        return HttpResponseForbidden("Not allowed.")

    room, _ = ChatRoom.objects.get_or_create(course=course)
    messages = room.messages.select_related("sender").order_by("-created_at")[:50]
    messages = list(messages)[::-1]
    return render(request, "forum.html", {"course": course, "messages": messages})
