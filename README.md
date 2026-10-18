# My Personalized Astrology Chat

A personalized AI chat application built with **FastAPI, Gemini, and Neo4j**. MyNaksh combines recent conversation history with persistent user memories to provide context-aware responses across chat sessions.

## Features

- **Conversational AI:** Generates responses using the Gemini API.
- **Persistent memory:** Stores user facts in Neo4j, organized by category and timeframe.
- **Memory updates:** Uses a stable memory key to update existing facts rather than creating a new memory for every correction.
- **Session history:** Retains recent turns within a session to support follow-up questions.
- **Context selection:** Selects a small set of relevant memories before generating a response.
- **Input validation:** Uses Pydantic models through FastAPI.
- **Automated tests:** Covers health checks, memory APIs, context selection, chat responses, and simulated AI failures.

## Architecture

```text
Client
  |
  v
FastAPI (app/main.py)
  |
  +--> Session Memory (app/session_memory.py)
  |      Recent conversation turns
  |
  +--> Neo4j (app/brain.py)
  |      Persistent user memories
  |
  +--> Context Selector (app/context_selector.py)
  |      Ranks memories by relevance
  |
  +--> Gemini (app/llm.py)
         Memory extraction and response generation
```

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic
- Google Gemini API
- Neo4j
- pytest and FastAPI TestClient

## Project Structure

```text
app/
  main.py              API routes and orchestration
  models.py            Request and response schemas
  brain.py             Neo4j persistence
  llm.py               Gemini integration
  session_memory.py    Recent conversation history
  context_selector.py  Memory relevance ranking

tests/
  test_main.py         Automated tests

.env                   Local credentials (not committed)
requirements.txt       Python dependencies
```

## Setup

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-flash-latest

NEO4J_URI=your_neo4j_uri
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j
```

Use your actual credentials locally. Never commit `.env` or expose API keys in logs.

### 4. Start the API

```powershell
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to explore the API using Swagger UI.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/memory` | Create or update a memory |
| GET | `/memory/{user_id}` | Retrieve a user's memories |
| POST | `/chat` | Generate a context-aware response |

### Example: Save a memory

```json
{
  "user_id": "demo_user",
  "text": "Planning to change careers next year",
  "category": "career",
  "timeframe": "next year"
}
```

Send this JSON to `POST /memory`.

### Example: Chat

```json
{
  "user_id": "demo_user",
  "session_id": "session_1",
  "message": "What should I focus on first?"
}
```

Send this JSON to `POST /chat`.

A response includes the generated answer, user and session IDs, and an indication of the context sources used.

## Running Tests

```powershell
python -m pytest -v
```

The test suite currently covers health checks, memory relevance, memory creation and retrieval, successful chat responses, simulated Gemini failures, memory-key response behavior, and session isolation.

## Design Decisions and Trade-offs

- **Neo4j for persistent memory:** Provides a graph database foundation for associating users with memories and extending the model with relationships later.
- **Stable memory keys:** Allow facts to be updated by identity rather than stored as unrelated duplicates.
- **Separate session and persistent memory:** Recent turns support immediate conversational continuity, while Neo4j supports recall across sessions.
- **Bounded context:** Only a limited number of selected memories are passed to the language model, helping control prompt size and reduce irrelevant context.
- **Mocked unit tests:** Most tests run without live Gemini or Neo4j dependencies, making the suite fast and repeatable.

## Current Limitations

- Session history is stored in process memory and is lost when the application restarts.
- The current memory selector uses keyword overlap and category keywords rather than semantic embeddings.
- Memory extraction and answer generation depend on the external Gemini service.
- Production deployment would need stronger concurrency handling, authentication, observability, and integration testing.

## Potential Improvements

- Add semantic retrieval and memory importance scoring.
- Add automated integration tests against a dedicated Neo4j test database.
- Persist session history if required.
- Introduce authentication, rate limiting, and structured logging.
- Add conflict handling and memory expiration policies.
