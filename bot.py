from aiogram import Bot, Dispatcher, types
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def get_file_id(message: types.Message):
    if message.video:
        await message.answer(f"file_id:\n{message.video.file_id}")
    elif message.document:
        await message.answer(f"file_id:\n{message.document.file_id}")
    else:
        await message.answer("Перешліть мені відео з каналу.")

async def main():
    await dp.start_polling(bot)

asyncio.run(main())
