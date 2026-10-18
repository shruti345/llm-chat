
import asyncio

from app.brain import get_driver, get_database_name


async def main():
    driver = get_driver()

    try:
        await driver.verify_connectivity()
        print("Neo4j connection successful!")

        async with driver.session(database=get_database_name()) as session:
            result = await session.run("RETURN 1 AS value")
            record = await result.single()
            print("Query result:", record["value"])
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(main())
