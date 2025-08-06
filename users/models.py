import random

from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Person(models.Model):
    ROLE_CHOICES = {
        "s": "Student",
        "p": "Professor",
        "t": "Teaching Assistant",
    }
    first_name = models.CharField(max_length=50, null=False, blank=False)
    last_name = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    date_joined = models.DateField(auto_now_add=True, null=False, blank=False)
    role = models.CharField(max_length=1, choices=ROLE_CHOICES)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=False, blank=False)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Professor(Person):
    pass

class TeachingAssistant(Person):
    course = models.ManyToManyField("courses.Course", blank=True)

class Student(Person):
    index = models.CharField(max_length=6, unique=True, null=False, blank=False)