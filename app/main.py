
import logging

from fastapi import FastAPI, HTTPException
from neo4j.exceptions import Neo4jError
from app.context_selector import select_relevant_memories

from app.brain import add_memory, get_memories, get_chat_memories, close_driver
from app.llm import generate_response, extract_memories
from app.models import (
    ChatRequest,
    ChatResponse,
    MemoryCreateRequest,
    MemoryItem,
    MemoryListResponse,
)
from app.session_memory import get_history, add_turn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MyNaksh Personalized Chat")

@app.on_event("shutdown")
async def shutdown_event():
    await close_driver()


@app.get("/health")
def health_check():
    return {"status": "ok"}


# @app.post("/memory", response_model=MemoryItem)
# async def create_memory(request: MemoryCreateRequest):
#     try:
#         memory = await add_memory(
#             user_id=request.user_id,
#             text=request.text,
#             category=request.category,
#             timeframe=request.timeframe,
#         )
#         return MemoryItem(**memory)
#     except (Neo4jError, RuntimeError):
#         logger.exception("Failed to save memory")
#         raise HTTPException(
#             status_code=503,
#             detail="The memory service is temporarily unavailable.",
#         )

@app.post("/memory", response_model=MemoryItem)
async def create_memory(request: MemoryCreateRequest):
    print("Received request:", request)

    memory = await add_memory(
        user_id=request.user_id,
        text=request.text,
        category=request.category,
        timeframe=request.timeframe,
    )

    print("Memory returned from Neo4j:", memory)

    return MemoryItem(**memory)

@app.get("/memory/{user_id}", response_model=MemoryListResponse)
async def list_memories(user_id: str):
    try:
        memories = await get_memories(user_id)
        return MemoryListResponse(
            user_id=user_id,
            memories=[MemoryItem(**item) for item in memories],
        )
    except (Neo4jError, RuntimeError):
        logger.exception("Failed to retrieve memories")
        raise HTTPException(
            status_code=503,
            detail="The memory service is temporarily unavailable.",
        )




@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # 1. Retrieve short-term conversation history.
    history = get_history(request.user_id, request.session_id)

    # 2. Extract and save useful facts from the user's message.
    #    If extraction fails, continue with the chat.
    
    # 1. Retrieve existing persistent memories for comparison.
    try:
        memories = await get_chat_memories(
            user_id=request.user_id,
            limit=50,
        )
    except Exception:
        logger.exception("Neo4j memory retrieval failed")
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve persistent memories.",
        )

    # 2. Extract new facts or corrections.
    try:
        extracted_memories = await extract_memories(
            request.message,
            existing_memories=memories,
        )

        for memory in extracted_memories:
            await add_memory(
                user_id=request.user_id,
                text=memory["text"],
                category=memory["category"],
                timeframe=memory["timeframe"],
                memory_key=memory["memory_key"],
            )

    except Exception:
        logger.exception("Automatic memory extraction or saving failed")

    # 3. Retrieve the latest versions for response generation.
    try:
        memories = await get_chat_memories(
            user_id=request.user_id,
            limit=50,
        )
    except Exception:
        logger.exception("Neo4j memory retrieval failed after extraction")
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve persistent memories.",
        )

    # Keep your existing generate_response(), add_turn(),
    # context_used, and ChatResponse code below this section.

    # Select only memories relevant to the current message.
    selected_memories = select_relevant_memories(
        message=request.message,
        memories=memories,
        limit=5,
    )

    # 4. Generate a response using history and persistent memories.
    try:
        answer = await generate_response(
            message=request.message,
            history=history,
            memories=selected_memories,
        )
    except Exception:
        logger.exception("Gemini response generation failed")
        raise HTTPException(
            status_code=502,
            detail="The AI service could not generate a response.",
        )

    # 5. Save the completed turn in short-term session memory.
    add_turn(
        user_id=request.user_id,
        session_id=request.session_id,
        user_message=request.message,
        assistant_message=answer,
    )

    # 6. Report which context sources were used.
    context_used = []

    if history:
        context_used.append("recent_conversation")

    if selected_memories:
        context_used.append("persistent_memory")

    return ChatResponse(
        response=answer,
        user_id=request.user_id,
        session_id=request.session_id,
        context_used=context_used,
    )
