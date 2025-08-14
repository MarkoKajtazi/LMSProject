import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST

from courses.models import Course, Enrollment
from exams.models import Exam, ExamQuestion, StudentAnswer
from main.views import course
from users.models import Professor, Student, TeachingAssistant
from django.contrib import messages
from django.utils import timezone


# Create your views here.
@login_required
def grading_studio(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_prof = Course.objects.filter(pk=course_id, instructor__user=user).exists()
    is_ta = Course.objects.filter(pk=course_id, teaching_assistants__user=user).exists()
    is_student = Enrollment.objects.filter(course_id=course_id, student__user=user).exists()

    if not (is_prof | is_ta | is_student):
        return HttpResponseForbidden("You do not have access to this site.")

    courses = Course.objects.none()
    exams = Exam.objects.none()

    if user.is_authenticated:
        courses = Course.objects.filter(
            Q(instructor__user=user) |
            Q(teaching_assistants__user=user) |
            Q(enrollment__student__user=user)
        ).distinct().order_by("name")

        exams = Exam.objects.filter(
            Q(course_id__exact=course_id),
            Q(course__instructor__user=user) |
            Q(registrations__student__user=user),
        ).distinct().order_by("title")

    context = {
        "course": course,
        "courses": courses,
        "exams": exams,
        "is_prof": Professor.objects.filter(user=user).exists(),
        "is_student": Student.objects.filter(user=user).exists(),
        "is_ta": TeachingAssistant.objects.filter(user=user).exists(),
    }

    return render(request, "grading_studio/studio_home.html", context=context)


@login_required
def exam_student(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    course_id = exam.course_id
    user = request.user

    is_student = Enrollment.objects.filter(course_id=course_id, student__user=user).exists()

    if not is_student:
        return HttpResponseForbidden("You do not have access to this site.")

    student = get_object_or_404(Student, user=user) if is_student else None

    context = {
        "exam": exam,
    }

    return render(request, "grading_studio/exam.html", context=context)

@login_required
@require_GET
def answer_status(request, question_id: int):
    """
    GET /api/questions/<question_id>/answer-status/
    Returns whether the *current student* has an answer for the given question.
    """
    # Expect a OneToOne relation: User -> Student as `user.student`
    student = getattr(request.user, "student", None)
    if student is None:
        return JsonResponse({"error": "Current user is not a Student."}, status=403)

    try:
        q = ExamQuestion.objects.select_related("exam").get(pk=question_id)
    except ExamQuestion.DoesNotExist:
        raise Http404("Question not found.")

    ans = (
        StudentAnswer.objects
        .filter(question=q, student=student)
        .order_by("-answer_date")
        .first()
    )

    if ans:
        payload = {
            "question_id": q.id,
            "exam_id": q.exam_id,
            "has_answer": True,
            "answer": {
                "id": ans.id,
                "answer": ans.answer,
                "scored": ans.scored,
                "answer_date": ans.answer_date.isoformat(),
            },
        }
    else:
        payload = {
            "question_id": q.id,
            "exam_id": q.exam_id,
            "has_answer": False,
            "answer": None,
        }

    return JsonResponse(payload)

@require_GET
def questions_by_exam(request, exam_id: int):
    exam = get_object_or_404(Exam, pk=exam_id)
    questions_qs = (
        exam.questions
        .order_by("order", "id")
        .values("id", "order", "question", "max_score")
    )
    return JsonResponse(
        {
            "exam_id": exam.id,
            "title": exam.title,
            "count": questions_qs.count(),
            "questions": list(questions_qs),
        }
    )

@login_required
@require_POST
def submit_answer(request, question_id: int):
    # Must be a Student
    student = getattr(request.user, "student", None)
    if student is None:
        return JsonResponse({"error": "Current user is not a Student."}, status=403)

    # Valid question
    try:
        q = ExamQuestion.objects.select_related("exam__course").get(pk=question_id)
    except ExamQuestion.DoesNotExist:
        raise Http404("Question not found.")

    # Must be enrolled in the course that owns the exam
    if not Enrollment.objects.filter(course=q.exam.course, student=student).exists():
        return JsonResponse({"error": "You are not enrolled in this course."}, status=403)

    # Parse body (JSON or form)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        payload = request.POST
    answer_text = (payload.get("answer") or "").strip()
    if not answer_text:
        return JsonResponse({"error": "Answer is required."}, status=400)

    # Create or update (blocked if already scored)
    ans, created = StudentAnswer.objects.get_or_create(
        question=q, student=student,
        defaults={"answer": answer_text, "answer_date": timezone.now(), "exam": q.exam,}
    )
    if not created:
        if ans.scored:
            return JsonResponse({"error": "Answer already scored and cannot be changed."}, status=409)
        ans.exam = q.exam
        ans.answer = answer_text
        ans.answer_date = timezone.now()
        ans.save()

    return JsonResponse({
        "ok": True,
        "created": created,
        "answer": {
            "id": ans.id,
            "answer": ans.answer,
            "scored": ans.scored,
            "answer_date": ans.answer_date.isoformat(),
        }
    }, status=201 if created else 200)