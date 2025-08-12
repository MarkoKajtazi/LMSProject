# courses/forms.py
from django import forms
from django.utils import timezone

from .models import Course, Enrollment


class CourseForm(forms.ModelForm):
    credits = forms.IntegerField(min_value=1, max_value=6)

    class Meta:
        model = Course
        fields = ["name", "description", "credits", "instructor"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

# Variant for professors: instructor is set in the view, not shown in the form
class CourseFormForProfessor(forms.ModelForm):
    credits = forms.IntegerField(min_value=1, max_value=60)

    class Meta:
        model = Course
        fields = ["name", "description", "credits"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["enroll_date"]  # student & course are set in the view
        widgets = {
            "enroll_date": forms.DateInput(attrs={"type": "date"})
        }

    def __init__(self, *args, student=None, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student
        self.course = course
        self.fields["enroll_date"].initial = timezone.now().date()

    def clean(self):
        cleaned = super().clean()
        if self.student and self.course:
            exists = Enrollment.objects.filter(student=self.student, course=self.course).exists()
            if exists:
                raise forms.ValidationError("You are already enrolled in this course.")
        return cleaned

class EnrollmentPickCourseForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none())

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Course.objects.all()
        if student:
            # hide courses already enrolled
            qs = qs.exclude(enrollment__student=student)
        self.fields["course"].queryset = qs.order_by("name")