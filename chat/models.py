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

class ChatReadState(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="read_states")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_read_states")
    last_read_at = models.DateTimeField(null=True, blank=True)
    last_read_message = models.ForeignKey(ChatMessage, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("room", "user")

    def __str__(self):
        who = getattr(self.user, "username", "user")
        return f"{who} in room {self.room_id}"