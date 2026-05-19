"""
Utility functions for the Smart AI Assistant.
"""

from datetime import datetime


def export_chat(messages, format="txt"):
    """
    Convert chat messages to downloadable text.
    messages: list of dicts with keys 'role' and 'content'
    format: 'txt' or 'md'
    """
    lines = []

    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"]

        if format == "md":
            if role == "User":
                lines.append(f"## 🧑 User\n\n{content}\n")
            else:
                lines.append(f"## 🤖 Assistant\n\n{content}\n")
        else:
            lines.append(f"{role}: {content}\n")

    return "\n".join(lines)


def get_word_count(messages):
    """Approximate usage by counting words in all messages."""
    total_words = 0
    for msg in messages:
        total_words += len(msg["content"].split())
    return total_words


def get_session_start():
    """Return a timestamp string for session start."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_timestamp(dt_string):
    """Convert an ISO timestamp string to a human-friendly format."""
    try:
        dt = datetime.fromisoformat(dt_string)
        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                mins = diff.seconds // 60
                return f"{mins}m ago"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days}d ago"
        else:
            return dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return str(dt_string)


def truncate_text(text, max_length=80):
    """Truncate text with ellipsis for previews."""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def generate_chat_title(first_message):
    """Generate a conversation title from the first user message."""
    # Take first 50 chars, clean up
    title = first_message.strip()[:50]
    # Remove newlines
    title = title.replace("\n", " ").replace("\r", "")
    # Add ellipsis if truncated
    if len(first_message.strip()) > 50:
        title += "..."
    return title if title else "New Chat"