from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from courses.models import Course
from exams.models import Exam, StudentAnswer


# Create your views here.
@login_required
def grading_exam_page(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    submissions = StudentAnswer.objects.filter(exam=exam)

    context = {
        'exam': exam,
        'submissions': submissions,
    }

    return render(request, 'grading_studio/exam_grading.html', context=context)