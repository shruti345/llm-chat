
import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )

model_name = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
client = genai.Client(api_key=api_key)

SYSTEM_INSTRUCTION = """
You are MyNaksh, a warm and helpful personalized assistant.

Use the recent conversation to understand follow-up questions.
Do not invent personal facts about the user or claim to know
their birth chart when the required information has not been provided.
If relevant information is missing, ask a concise clarifying question.
Give clear, practical answers and distinguish general guidance
from astrology-specific interpretations.
"""


async def generate_response(
    message: str,
    history: list[dict[str, str]] | None = None,
    memories: list[dict] | None = None,
) -> str:
    """Generate a response using conversation history and saved memories."""
    contents = []

    # Short-term memory: previous messages from this session.
    for item in history or []:
        contents.append(
            types.Content(
                role=item["role"],
                parts=[types.Part.from_text(text=item["text"])],
            )
        )

    # Long-term memory: persistent facts saved in Neo4j.
    memory_context = ""
    if memories:
        memory_lines = [
            (
                f"- {item['text']} "
                f"(category: {item['category']}, "
                f"timeframe: {item.get('timeframe') or 'unspecified'})"
            )
            for item in memories
        ]

        memory_context = (
            "Relevant saved information about this user follows. "
            "Use it when helpful, but do not assume it is relevant "
            "to every question. If facts conflict, ask for clarification.\n"
            + "\n".join(memory_lines)
        )

    current_message = message
    if memory_context:
        current_message = (
            f"{memory_context}\n\n"
            f"Current user message: {message}"
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=current_message)],
        )
    )

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    answer = response.text
    if not answer:
        raise RuntimeError("Gemini returned an empty response.")

    return answer.strip()


async def extract_memories(
    message: str,
    existing_memories: list[dict] | None = None,
) -> list[dict]:
    """Extract useful facts and identify updates to existing facts."""
    import json

    existing = [
        {
            "memory_key": item.get("memory_key"),
            "text": item.get("text"),
            "category": item.get("category"),
            "timeframe": item.get("timeframe"),
        }
        for item in (existing_memories or [])
    ]

    prompt = f"""
You extract persistent user memories for a personalized assistant.

Existing memories:
{json.dumps(existing, ensure_ascii=False)}

New user message:
{message}

Rules:
- Extract only useful personal facts explicitly stated or corrected
  by the user in the new message.
- Do not extract facts from questions, hypotheticals, or assumptions.
- Ignore ordinary questions that reveal no useful personal fact.
- If the user corrects or changes an existing fact, reuse its
  memory_key so the existing memory can be updated.
- For a new fact, create a short, stable, descriptive memory_key
  in lowercase snake_case, such as career_plan or answer_style.
- Do not reuse a key for unrelated facts.
- Extract at most 5 facts.
- Use only these categories: career, preference, interest,
  profile, astrology, other.
- Use null for timeframe when none is stated.
- Return only valid JSON in this exact shape:

{{
  "memories": [
    {{
      "memory_key": "career_plan",
      "text": "The user's current career plan",
      "category": "career",
      "timeframe": null
    }}
  ]
}}

Return {{"memories": []}} if there is nothing worth saving.
"""

    response = await client.aio.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        return []

    try:
        data = json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(data, dict):
        return []

    raw_memories = data.get("memories", [])
    if not isinstance(raw_memories, list):
        return []

    allowed_categories = {
        "career", "preference", "interest",
        "profile", "astrology", "other",
    }

    memories = []

    for item in raw_memories[:5]:
        if not isinstance(item, dict):
            continue

        text = item.get("text")
        key = item.get("memory_key")
        category = item.get("category", "other")
        timeframe = item.get("timeframe")

        if not isinstance(text, str) or not text.strip():
            continue

        if not isinstance(key, str) or not key.strip():
            continue

        if category not in allowed_categories:
            category = "other"

        if timeframe is not None and not isinstance(timeframe, str):
            timeframe = None

        memories.append({
            "memory_key": key.strip().lower()[:100],
            "text": text.strip()[:2000],
            "category": category,
            "timeframe": timeframe,
        })

    return memories
