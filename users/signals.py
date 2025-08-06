import random

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Student, Professor, TeachingAssistant


@receiver(pre_save, sender=Student)
def create_user_for_student(sender, instance, **kwargs):
    print("stu signal ACTIVATED")
    if not instance.user_id:
        while True:
            generated = f"{random.randint(100000, 999999)}"
            if not Student.objects.filter(index=generated).exists():
                instance.index = generated
                break

        user = User.objects.create_user(
            first_name=instance.first_name,
            last_name=instance.last_name,
            username = instance.index,
            email = instance.email,
            password = "student123"
        )
        instance.user = user
        instance.role = 's'

        group, created = Group.objects.get_or_create(name='Students')
        user.groups.add(group)

@receiver(pre_save, sender=Professor)
def create_user_for_professor(sender, instance, **kwargs):
    print("prof signal ACTIVATED")
    if not instance.user_id:
        user = User.objects.create_user(
            first_name=instance.first_name,
            last_name=instance.last_name,
            username = instance.email,
            email = instance.email,
            password = "professor123"
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        instance.user = user
        instance.role = 'p'

        group, created = Group.objects.get_or_create(name='Professors')
        user.groups.add(group)

@receiver(pre_save, sender=TeachingAssistant)
def create_user_for_ta(sender, instance, **kwargs):
    print("ta signal ACTIVATED")
    if not instance.user_id:
        user = User.objects.create_user(
            first_name=instance.first_name,
            last_name=instance.last_name,
            username = instance.email,
            email = instance.email,
            password = "ta123"
        )
        user.is_staff = True
        user.save()

        instance.user = user
        instance.role = 't'

        group, created = Group.objects.get_or_create(name='Teaching Assistants')
        user.groups.add(group)