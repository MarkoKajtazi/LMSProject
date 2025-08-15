"""
URL configuration for LMSProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
import main.views as main
import chat.views as chat
from django.contrib.auth.views import LogoutView
import courses.views as courses
import exams.views as exams
import assistant.views as assistant

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main.home, name='home'),
    path('courses/<int:course_id>/', main.course, name='course'),
    path("courses/<int:course_id>/chat/", chat.course_chat, name="course_chat"),
    path('courses/new/', courses.course_create, name='course_create'),
    path("courses/enroll/", courses.enroll_choose_course, name="course_enroll_choose"),

    path("accounts/", include("django.contrib.auth.urls")),
    path('accounts/logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('grading/<int:course_id>/', exams.grading_studio, name='grading_studio'),
    path('grading/exams/<int:exam_id>/', exams.exam_student, name='exam_student'),
    path("api/exams/<int:exam_id>/questions/", exams.questions_by_exam, name="questions_by_exam"),
    path("api/questions/<int:question_id>/answer-status/", exams.answer_status, name="answer_status"),
    path("api/questions/<int:question_id>/answers/", exams.submit_answer, name="submit_answer"),

    path("assistant/response/", assistant.response, name="assistant_response"),
    path("assistant/chat/", assistant.chat_page, name="assistant_chat_page"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
