
import re


CATEGORY_KEYWORDS = {
    "career": {
        "career", "job", "work", "role", "company", "interview",
        "salary", "promotion", "manager", "profession", "switch",
        "resume", "employment", "goal",
    },
    "preference": {
        "prefer", "preference", "like", "dislike", "style",
        "language", "format", "concise", "detailed",
    },
    "interest": {
        "interest", "hobby", "music", "guitar", "singing",
        "sport", "travel", "book",
    },
    "profile": {
        "name", "age", "birthday", "birth", "born", "location",
        "city", "country", "language",
    },
    "astrology": {
        "astrology", "zodiac", "horoscope", "sun", "moon",
        "chart", "nakshatra", "planet", "kundli",
    },
}

STOP_WORDS = {
    "what", "when", "where", "which", "who", "why", "how",
    "have", "has", "had", "does", "did", "are", "was", "were",
    "the", "and", "for", "with", "from", "about", "tell",
    "me", "my", "you", "your", "that", "this", "can", "could",
    "would", "should", "please", "user",
}


def tokenize(text: str) -> set[str]:
    """Convert text to lowercase words, ignoring common stop words."""
    words = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def select_relevant_memories(
    message: str,
    memories: list[dict],
    limit: int = 5,
) -> list[dict]:
    """Rank saved memories against the current user message."""
    if not memories or limit <= 0:
        return []

    message_words = tokenize(message)
    ranked = []

    for index, memory in enumerate(memories):
        memory_words = tokenize(memory.get("text", ""))
        category = memory.get("category", "other")

        # Exact word overlap gives a basic relevance score.
        score = len(message_words & memory_words)

        # Boost memories whose category matches the topic.
        category_words = CATEGORY_KEYWORDS.get(category, set())
        if message_words & category_words:
            score += 3

        # Small bonus when the message explicitly mentions
        # the memory's category.
        if category in message_words:
            score += 2

        ranked.append((score, index, memory))

    # Higher relevance first; preserve original order for ties.
    ranked.sort(key=lambda item: (-item[0], item[1]))

    # Avoid injecting unrelated memories when nothing matches.
    relevant = [
        memory for score, _, memory in ranked
        if score > 0
    ]

    return relevant[:limit]
