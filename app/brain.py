
import os

from dotenv import load_dotenv
from neo4j import AsyncGraphDatabase

load_dotenv()

_driver = None


def get_driver():
    """Create the shared database driver on first use."""
    global _driver

    if _driver is None:
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")

        if not all([uri, username, password]):
            raise RuntimeError(
                "Set NEO4J_URI, NEO4J_USERNAME, and "
                "NEO4J_PASSWORD in .env"
            )

        _driver = AsyncGraphDatabase.driver(
            uri,
            auth=(username, password),
        )

    return _driver


def get_database_name() -> str:
    return os.getenv("NEO4J_DATABASE", "neo4j")


async def close_driver() -> None:
    """Close the connection pool when the application shuts down."""
    global _driver

    if _driver is not None:
        await _driver.close()
        _driver = None


async def add_memory(
    user_id: str,
    text: str,
    category: str,
    timeframe: str | None = None,
    memory_key: str = "general",
) -> dict:
    """Create or update a user's memory using a stable key."""
    driver = get_driver()

    query = """
    MERGE (u:User {user_id: $user_id})
    ON CREATE SET u.created_at = datetime()

    MERGE (m:Memory {
        user_id: $user_id,
        memory_key: $memory_key
    })
    ON CREATE SET m.created_at = datetime()

    SET m.text = $text,
        m.category = $category,
        m.timeframe = $timeframe,
        m.updated_at = datetime()

    MERGE (u)-[:HAS_MEMORY]->(m)

    RETURN m.text AS text,
           m.category AS category,
           m.timeframe AS timeframe,
           m.memory_key AS memory_key
    """

    async with driver.session(database=get_database_name()) as session:
        result = await session.run(
            query,
            user_id=user_id,
            text=text,
            category=category,
            timeframe=timeframe,
            memory_key=memory_key,
        )
        record = await result.single()

        if record is None:
            raise RuntimeError("Neo4j did not return the saved memory.")

        return dict(record)

async def get_memories(user_id: str) -> list[dict]:
    """Retrieve memories belonging to one user."""
    driver = get_driver()

    query = """
    MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY]->(m:Memory)
    RETURN m.text AS text,
           m.category AS category,
           m.timeframe AS timeframe,
           m.memory_key AS memory_key
    ORDER BY m.updated_at DESC
    LIMIT 50
    """

    async with driver.session(database=get_database_name()) as session:
        result = await session.run(query, user_id=user_id)
        records = await result.data()

    return records


async def get_chat_memories(
    user_id: str,
    limit: int = 10,
) -> list[dict]:
    """Retrieve a small set of persistent memories for chat."""
    driver = get_driver()

    query = """
    MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY]->(m:Memory)
    RETURN m.text AS text,
           m.category AS category,
           m.timeframe AS timeframe,
           m.memory_key AS memory_key
    ORDER BY m.updated_at DESC
    LIMIT $limit
    """

    async with driver.session(database=get_database_name()) as session:
        result = await session.run(
            query,
            user_id=user_id,
            limit=limit,
        )
        records = await result.data()

    return records
