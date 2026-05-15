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
                lines.append(f"## User\n\n{content}\n")
            else:
                lines.append(f"## Assistant\n\n{content}\n")
        else:
            lines.append(f"{role}: {content}\n")

    return "\n".join(lines)


def get_word_count(messages):
    """
    Approximate usage by counting words in all messages.
    """
    total_words = 0
    for msg in messages:
        total_words += len(msg["content"].split())
    return total_words


def get_session_start():
    """
    Return a timestamp string for session start.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")