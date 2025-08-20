# chat/services.py
from typing import List, Optional
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from .models import ChatRoom, ChatMessage, ChatReadState

# --- LLM helpers -------------------------------------------------------------

def _use_ollama() -> bool:
    try:
        import ollama  # noqa: F401
        return True
    except Exception:
        return False

def llm_summarize(markdown_input: str, system_hint: str | None = None) -> str:
    system = system_hint or (
        "You summarize course chat rooms. Output concise sections: "
        "Summary, Decisions, Action Items (owners), Questions. ≤200 words."
    )

    text = None

    # --- Try Ollama first (supports both chat() and generate() shapes) ---
    try:
        import ollama
        # Prefer chat API
        resp = ollama.chat(
            model=getattr(settings, "OLLAMA_MODEL", "llama3"),
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": markdown_input}],
        )
        print(f"inputs are {markdown_input}")

        text = (resp.get("message") or {}).get("content")
        # Fallback if someone wired generate() instead of chat()
        if not text and "response" in resp:
            text = resp["response"]
    except Exception:
        # Ignore and try OpenAI
        pass

    # Final guard: never return None
    return (text or "No unread messages.").strip()

# --- Unread logic ------------------------------------------------------------
def _format_messages_for_llm(messages: List[ChatMessage]) -> str:
    lines = []
    for m in messages:
        sender = (m.sender.get_full_name() or m.sender.username or str(m.sender)).strip()
        # keep each line reasonably short
        content = (m.content or "").strip()
        if len(content) > 600:
            content = content[:600] + "…"
        lines.append(f"- [{m.created_at:%Y-%m-%d %H:%M}] {sender}: {content}")
    return "\n".join(lines)

def get_unread_messages(room: ChatRoom, user, limit: int = 100) -> List[ChatMessage]:
    state, _ = ChatReadState.objects.get_or_create(room=room, user=user)
    qs = room.messages.all()
    if state.last_read_at:
        qs = qs.filter(created_at__gt=state.last_read_at)
    # Always return in ascending time (your model Meta already orders by created_at)
    return list(qs.select_related("sender")[:limit])

def mark_room_read(room: ChatRoom, user, up_to: Optional[ChatMessage] = None) -> None:
    state, _ = ChatReadState.objects.get_or_create(room=room, user=user)
    if up_to is None:
        up_to = room.messages.order_by("-created_at").first()
    if up_to:
        state.last_read_at = up_to.created_at
        state.last_read_message = up_to
        state.save(update_fields=["last_read_at", "last_read_message"])

def summarize_unread(room, user, limit: int = 100, mark_as_read: bool = True) -> str:
    unread = get_unread_messages(room, user, limit=limit)
    if not unread:
        return "No unread messages."
    header = f"Course room: {getattr(room.course, 'name', getattr(room.course, 'title', 'Course'))}\n"
    header += f"Unread count: {len(unread)} (showing up to {limit})\n\n"
    body = _format_messages_for_llm(unread)
    summary = llm_summarize(header + "Summarize the following messages:\n\n" + body)
    if mark_as_read:
        mark_room_read(room, user, up_to=unread[-1])

    print(summary)
    return summary or "No unread messages."
