import asyncio
from app.brain import add_memory, close_driver

async def main():
    try:
        result = await add_memory(
            user_id="debug-user",
            text="Testing Neo4j memory write",
            category="career",
            timeframe="next year",
        )
        print("Memory saved successfully:", result)
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        await close_driver()

if __name__ == "__main__":
    asyncio.run(main())