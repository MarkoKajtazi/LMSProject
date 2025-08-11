from django.db import models
from django.conf import settings

class ChatRoom(models.Model):
    course = models.OneToOneField(
        "courses.Course", on_delete=models.CASCADE, related_name="chat_room"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Room for {self.course.title}"

class ChatMessage(models.Model):
    room   = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_messages")
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


    def __str__(self):
        return f"{self.sender.first_name}: {self.content[:20]}"
