import os
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

TOKEN = os.getenv("BOT_TOKEN")
PIN_CODE = os.getenv("PIN_CODE", "1234")

LESSONS = {
    "lesson_1": {
        "title": "Подкаст з юристом",
        "file_id": "BAACAgIAAxkBAAMSaghlgxDsMKMDoNnUIiUS6OVSDoYAAvqcAAL2cQABSb00s6elWfjtOwQ",
        "file_id": "BQACAgIAAyEFAATi_-lbAAMXaghAghVRJdqWl-qJ2yTn6mjBYDoAAg2dAAIbZElI1COFJhYDm1k7BA"
    },
    "lesson_2": {
        "title": "Урок 2",
        "file_id": "BAACAgIAAxkBAAMQaghleSVDx79dp5Ei00qN4DjHP4kAAnOVAAIJlZBJSRVOh6Laheo7BA"
    },
    "lesson_3": {
        "title": "Урок 3",
        "file_id": "BAACAgIAAyEFAATi_-lbAAMVaghAGdmQ8qlSozeLkqn9gV5_Y8UAAkelAAKp9IlLShFmtja0j3A7BA"
    }
}

USERS_FILE = "users.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()


def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(list(users), file)


activated_users = load_users()


def lessons_keyboard():
    buttons = [
        [InlineKeyboardButton(text=data["title"], callback_data=key)]
        for key, data in LESSONS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id in activated_users:
        await message.answer(
            "Ви вже активовані ✅\nОберіть урок:",
            reply_markup=lessons_keyboard()
        )
    else:
        await message.answer("Введіть PIN-код для активації:")


@dp.message()
async def check_pin(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id in activated_users:
        await message.answer(
            "Оберіть урок:",
            reply_markup=lessons_keyboard()
        )
        return

    if message.text == PIN_CODE:
        activated_users.add(user_id)
        save_users(activated_users)

        await message.answer(
            "Активація успішна ✅\nТепер оберіть урок:",
            reply_markup=lessons_keyboard()
        )
    else:
        await message.answer("Невірний PIN-код. Спробуйте ще раз.")


@dp.callback_query()
async def send_lesson(callback: CallbackQuery):
    user_id = str(callback.from_user.id)

    if user_id not in activated_users:
        await callback.message.answer("Спочатку введіть PIN-код через /start")
        await callback.answer()
        return

    lesson = LESSONS.get(callback.data)

    if not lesson:
        await callback.answer("Урок не знайдено")
        return

    await callback.message.answer_video(
        video=lesson["file_id"],
        caption=lesson["title"]
    )

    await callback.answer()


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN не знайдено. Додайте його в Railway Variables.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
