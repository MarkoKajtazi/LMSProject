from django import forms
from .models import Exam, ExamQuestion


class ExamForm(forms.ModelForm):
    exam_date = forms.DateTimeInput()

    class Meta:
        model = Exam
        fields = ["course", "title", "description", "exam_type", "exam_date", "max_score"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "exam_type": forms.Select(attrs={"class": "form-select"}),
            # HTML5 datetime-local (Django won't auto-parse TZ; OK for admin/prof usage)
            "exam_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "max_score": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "course": forms.Select(attrs={"class": "form-select"}),
        }


from django.forms import inlineformset_factory

ExamQuestionFormSet = inlineformset_factory(
    Exam,
    ExamQuestion,
    fields=["question", "max_score", "order"],
    widgets={
        "question": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Question text…"}),
        "max_score": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        "order": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
    },
    extra=1,  # show 3 empty rows by default
    can_delete=True,  # allow removing questions
)


class ExamChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Exam) -> str:
        # Nice label: "<Title> — <Type> — <YYYY-MM-DD HH:MM>"
        return f"{obj.title} — {obj.get_exam_type_display()} — {obj.exam_date:%Y-%m-%d %H:%M}"

class ExamPickForm(forms.Form):
    exam = ExamChoiceField(
        queryset=Exam.objects.none(),
        empty_label="— Select an exam —",
        widget=forms.Select(attrs={"class": "form-select w-auto", "style": "min-width: 28rem; height: 40px"})
    )

    def __init__(self, *args, student=None, course=None, **kwargs):
        """
        Populate the dropdown with exams for `course`, excluding ones the student already registered for.
        """
        super().__init__(*args, **kwargs)
        qs = Exam.objects.none()
        if course is not None:
            qs = Exam.objects.filter(course=course).order_by("exam_date")
            if student is not None:
                qs = qs.exclude(registrations__student=student)
        self.fields["exam"].queryset = qs