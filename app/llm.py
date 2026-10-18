
import os

from dotenv import load_dotenv
from google import genai

# Load variables from the project's .env file.
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )

model_name = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-latest",
)

# Create one reusable client instead of creating one per request.
client = genai.Client(api_key=api_key)


async def generate_response(message: str) -> str:
    """Generate an answer using Gemini."""
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=message,
    )

    answer = response.text
    if not answer:
        raise RuntimeError("Gemini returned an empty response.")

    return answer.strip()
