from logger import logger
import server
import asyncio
import bot


async def main():
    bot_task = asyncio.create_task(bot.start())
    server_task = asyncio.create_task(server.start())

    await asyncio.gather(bot_task, server_task)


if __name__ == "__main__":
    asyncio.run(main())
