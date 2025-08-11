import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.shortcuts import get_object_or_404
from courses.models import Course
from .models import ChatRoom, ChatMessage
from .acl import user_can_access_course_room

class PingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({"ok": True})

class CourseChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.course_id = int(self.scope["url_route"]["kwargs"]["course_id"])
        self.group_name = f"course_chat_{self.course_id}"
        user = self.scope["user"]
        if not user.is_authenticated:
            return await self.close(code=4001)

        course = await sync_to_async(lambda: get_object_or_404(Course, pk=self.course_id))()
        allowed = await sync_to_async(user_can_access_course_room)(user, course)
        if not allowed:
            return await self.close(code=4003)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data or "{}")
        content = (data.get("message") or "").strip()
        if not content:
            return

        user = self.scope["user"]
        room = await sync_to_async(self._get_or_create_room)()

        msg = await sync_to_async(ChatMessage.objects.create)(
            room=room, sender=user, content=content
        )

        name = await sync_to_async(self._display_name)(user)
        out = {
            "id": msg.id,
            "sender": name,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        await self.channel_layer.group_send(self.group_name, {"type": "chat.message", "message": out})

    def _get_or_create_room(self):
        course = Course.objects.get(pk=self.course_id)
        room, _ = ChatRoom.objects.get_or_create(course=course)
        return room

    def _display_name(self, user):
        # prefer profile names if present; otherwise fallback to Django’s user fields
        for rel in ("student", "professor", "teachingassistant"):
            prof = getattr(user, rel, None)
            if prof:
                full = f"{getattr(prof, 'first_name','').strip()} {getattr(prof, 'last_name','').strip()}".strip()
                if full:
                    return full
        full = (getattr(user, "get_full_name", lambda: "")() or "").strip()
        return full or getattr(user, "username", "User")

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
