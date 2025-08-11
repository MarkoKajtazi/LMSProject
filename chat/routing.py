# chat/routing.py
from django.urls import re_path
from . import consumers
from .consumers import PingConsumer

websocket_urlpatterns = [
    re_path(r"^ws/ping/$", PingConsumer.as_asgi()),
    re_path(r"^ws/courses/(?P<course_id>\d+)/chat/$", consumers.CourseChatConsumer.as_asgi()),
]
