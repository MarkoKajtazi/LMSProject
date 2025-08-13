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
            "name": forms.TextInput(attrs={"rows": 4, "class":"form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class":"form-control"}),
            "credits": forms.NumberInput(attrs={"rows": 4, "class":"form-control"}),
        }


class EnrollmentPickCourseForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), empty_label="— Select a course —", widget=forms.Select(attrs={"class": "form-select w-auto", "style": "min-width: 28rem; height: 40px"}))

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Course.objects.all()
        if student:
            # hide courses already enrolled
            qs = qs.exclude(enrollment__student=student)
        self.fields["course"].queryset = qs.order_by("name")