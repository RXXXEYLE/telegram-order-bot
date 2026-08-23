import asyncio
import os

from aiogram import Bot


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))

    me = await bot.get_me()

    print("БОТ НАЙДЕН!")
    print("ID:", me.id)
    print("NAME:", me.first_name)
    print("USERNAME:", me.username)

    await bot.session.close()


asyncio.run(main())
