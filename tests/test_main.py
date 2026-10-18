
from fastapi.testclient import TestClient

from app.main import app
from app.context_selector import select_relevant_memories
from unittest.mock import AsyncMock, patch

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_irrelevant_memories_are_not_selected():
    memories = [
        {
            "text": "I am planning to change careers next year.",
            "category": "career",
            "timeframe": "next year",
        },
        {
            "text": "I enjoy playing guitar.",
            "category": "interest",
            "timeframe": None,
        },
    ]

    selected = select_relevant_memories(
        message="Explain binary search.",
        memories=memories,
        limit=5,
    )

    assert selected == []


def test_relevant_memory_is_selected():
    memories = [
        {
            "text": "I enjoy playing guitar.",
            "category": "interest",
            "timeframe": None,
        },
        {
            "text": "I am planning to change careers next year.",
            "category": "career",
            "timeframe": "next year",
        },
    ]

    selected = select_relevant_memories(
        message="What should I practice on guitar?",
        memories=memories,
        limit=5,
    )

    assert len(selected) == 1
    assert selected[0]["category"] == "interest"

def test_create_memory():
    fake_memory = {
        "text": "Planning to change careers next year",
        "category": "career",
        "timeframe": "next year",
        "memory_key": "career_plan",
    }

    with patch("app.main.add_memory", new_callable=AsyncMock) as mock_add:
        mock_add.return_value = fake_memory

        response = client.post(
            "/memory",
            json={
                "user_id": "test_user",
                "text": "Planning to change careers next year",
                "category": "career",
                "timeframe": "next year",
            },
        )

    assert response.status_code == 200
    assert response.json()["text"] == fake_memory["text"]
    assert response.json()["category"] == "career"
    mock_add.assert_awaited_once()


def test_list_memories():
    fake_memories = [
        {
            "text": "Planning to change careers next year",
            "category": "career",
            "timeframe": "next year",
            "memory_key": "career_plan",
        }
    ]

    with patch("app.main.get_memories", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_memories

        response = client.get("/memory/test_user")

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"
    assert len(data["memories"]) == 1
    assert data["memories"][0]["category"] == "career"
    mock_get.assert_awaited_once_with("test_user")

def test_chat_returns_response():
    with (
        patch(
            "app.main.get_chat_memories",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.main.extract_memories",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.main.generate_response",
            new_callable=AsyncMock,
            return_value="A hash map stores key-value pairs.",
        ) as mock_generate,
    ):
        response = client.post(
            "/chat",
            json={
                "user_id": "chat_test_user",
                "session_id": "chat_test_session",
                "message": "Explain hash maps.",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "A hash map stores key-value pairs."
    assert data["user_id"] == "chat_test_user"
    assert data["session_id"] == "chat_test_session"
    assert "persistent_memory" not in data["context_used"]
    mock_generate.assert_awaited_once()


def test_chat_returns_502_when_gemini_fails():
    with (
        patch(
            "app.main.get_chat_memories",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.main.extract_memories",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.main.generate_response",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Simulated Gemini failure"),
        ),
    ):
        response = client.post(
            "/chat",
            json={
                "user_id": "error_test_user",
                "session_id": "error_test_session",
                "message": "Explain hash maps.",
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The AI service could not generate a response."
    )


def test_memory_correction_uses_same_memory_key():
    from app.brain import add_memory

    with patch(
        "app.main.add_memory",
        new_callable=AsyncMock,
    ) as mock_add:
        mock_add.return_value = {
            "text": "I plan to change careers in 2027.",
            "category": "career",
            "timeframe": "2027",
            "memory_key": "career_plan",
        }

        response = client.post(
            "/memory",
            json={
                "user_id": "correction_test_user",
                "text": "I plan to change careers in 2027.",
                "category": "career",
                "timeframe": "2027",
            },
        )

    assert response.status_code == 200
    assert response.json()["memory_key"] == "career_plan"

    mock_add.assert_awaited_once_with(
        user_id="correction_test_user",
        text="I plan to change careers in 2027.",
        category="career",
        timeframe="2027",
    )


def test_session_histories_are_isolated():
    from app.session_memory import add_turn, get_history

    user_id = "session_isolation_user"

    add_turn(
        user_id,
        "session_A",
        "I enjoy guitar.",
        "That's a lovely hobby.",
    )

    add_turn(
        user_id,
        "session_B",
        "Explain binary search.",
        "Binary search halves the search space.",
    )

    history_a = get_history(user_id, "session_A")
    history_b = get_history(user_id, "session_B")

    assert len(history_a) == 2
    assert len(history_b) == 2

    assert history_a[0]["text"] == "I enjoy guitar."
    assert history_b[0]["text"] == "Explain binary search."

    assert all(
        turn["text"] != "I enjoy guitar."
        for turn in history_b
    )
