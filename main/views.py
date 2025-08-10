from django.shortcuts import render

from courses.models import Course


# Create your views here.
def home(request):
    courses=Course.objects.all()
    return render(request, "home.html", context={'courses': courses})

def course(request, course_id):
    c = Course.objects.get(pk=course_id)
    return render(request, "course.html", context={'course': c, "courses": Course.objects.all()})