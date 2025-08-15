# courses/forms.py
from django import forms
from django.utils import timezone

from .models import Course, Enrollment, CourseMaterial


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

class CourseMaterialForm(forms.ModelForm):
    # Use URLField to get real URL validation (model has TextField)
    url = forms.URLField(required=False, label="URL", widget=forms.URLInput(attrs={
        "class": "form-control", "placeholder": "https://…"
    }))

    class Meta:
        model = CourseMaterial
        fields = ["title", "material_type", "url", "upload"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "material_type": forms.Select(attrs={"class": "form-select"}),
            "upload": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_texts = {
            "url": "Required if type is Link.",
            "upload": "Upload a PDF file if type is PDF.",
        }

    def clean(self):
        cleaned = super().clean()
        mtype = cleaned.get("material_type")
        url = cleaned.get("url")
        upload = cleaned.get("upload")

        if mtype == CourseMaterial.PDF:
            if not upload:
                self.add_error("upload", "Upload is required for PDF materials.")
            if url:
                self.add_error("url", "Leave URL empty for PDF materials.")
        elif mtype == CourseMaterial.LINK:
            if not url:
                self.add_error("url", "URL is required for Link materials.")
            if upload:
                self.add_error("upload", "Do not upload a file for Link materials.")
        else:
            # Defensive: only PDF/Link are in choices
            self.add_error("material_type", "Unsupported material type.")
        return cleaned

    def clean_upload(self):
        f = self.cleaned_data.get("upload")
        mtype = self.cleaned_data.get("material_type") or self.data.get("material_type")
        if f and mtype == CourseMaterial.PDF and not f.name.lower().endswith(".pdf"):
            raise forms.ValidationError("Only PDF files are allowed for PDF materials.")
        return f


class EnrollmentPickCourseForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), empty_label="— Select a course —", widget=forms.Select(attrs={"class": "form-select w-auto", "style": "min-width: 28rem; height: 40px"}))

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Course.objects.all()
        if student:
            # hide courses already enrolled
            qs = qs.exclude(enrollment__student=student)
        self.fields["course"].queryset = qs.order_by("name")