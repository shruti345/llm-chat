
from fastapi import FastAPI

from app.models import ChatRequest, ChatResponse
from app.llm import generate_response

app = FastAPI(title="My Personalized Chat")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        answer = await generate_response(request.message)
    except Exception:
        logger.exception("Failed to generate a Gemini response")
        raise HTTPException(
            status_code=502,
            detail="The AI service could not generate a response. Please try again.",
        )

    return ChatResponse(
        response=answer,
        user_id=request.user_id,
        session_id=request.session_id,
        context_used=[],
    )
