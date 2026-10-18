
from collections import defaultdict
from threading import Lock

# Each entry is a list of Gemini-compatible role/text messages.
_MAX_TURNS = 5

_sessions: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
_lock = Lock()


def get_history(user_id: str, session_id: str) -> list[dict[str, str]]:
    """Return a copy of the recent history for this session."""
    key = (user_id, session_id)

    with _lock:
        return list(_sessions[key])


def add_turn(
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
) -> None:
    """Append one completed turn and retain only recent messages."""
    key = (user_id, session_id)

    with _lock:
        _sessions[key].extend([
            {"role": "user", "text": user_message},
            {"role": "model", "text": assistant_message},
        ])

        # Five turns = ten messages.
        _sessions[key] = _sessions[key][-_MAX_TURNS * 2:]
