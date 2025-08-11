from django.db.models.signals import post_save
from django.dispatch import receiver
from courses.models import Course
from .models import ChatRoom

@receiver(post_save, sender=Course)
def ensure_chat_room(sender, instance, created, **kwargs):
    if created:
        ChatRoom.objects.get_or_create(course=instance)
