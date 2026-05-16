import os
import asyncio
import asyncpg
import secrets
import string

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = os.getenv("ADMIN_ID")

LESSONS = {
    "lesson_1": {
        "title": "Тренінг",
        "files": [
            "BAACAgIAAxkBAAMSaghlgxDsMKMDoNnUIiUS6OVSDoYAAvqcAAL2cQABSb00s6elWfjtOwQ"
        ]
    },
    "lesson_2": {
        "title": "Розбори",
        "files": [
            "BAACAgIAAxkBAAMQaghleSVDx79dp5Ei00qN4DjHP4kAAnOVAAIJlZBJSRVOh6Laheo7BA"
        ]
    },
    "lesson_3": {
        "title": "Подкаст з юристом",
        "files": [
            "BAACAgIAAyEFAATi_-lbAAMVaghAGdmQ8qlSozeLkqn9gV5_Y8UAAkelAAKp9IlLShFmtja0j3A7BA",
            "BQACAgIAAyEFAATi_-lbAAMXaghAghVRJdqWl-qJ2yTn6mjBYDoAAg2dAAIbZElI1COFJhYDm1k7BA"
        ]
    }
}

bot = Bot(token=TOKEN)
dp = Dispatcher()
db_pool = None


def lessons_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=data["title"], callback_data=key)]
            for key, data in LESSONS.items()
        ]
    )


def generate_pin(length=10):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)

    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pins (
                code TEXT PRIMARY KEY,
                used_by BIGINT,
                used_username TEXT,
                used_at TIMESTAMP
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS activated_users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                activated_at TIMESTAMP DEFAULT NOW()
            );
        """)


async def is_user_activated(user_id: int) -> bool:
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT user_id FROM activated_users WHERE user_id = $1",
            user_id
        )
        return result is not None


async def activate_user_with_pin(user_id: int, username: str, pin: str) -> str:
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            code = await conn.fetchrow(
                "SELECT code, used_by FROM pins WHERE code = $1 FOR UPDATE",
                pin
            )

            if not code:
                return "invalid"

            if code["used_by"] is not None:
                return "used"

            await conn.execute(
                """
                UPDATE pins
                SET used_by = $1, used_username = $2, used_at = NOW()
                WHERE code = $3
                """,
                user_id,
                username,
                pin
            )

            await conn.execute(
                """
                INSERT INTO activated_users (user_id, username)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
                username
            )

            return "activated"


@dp.message(Command("myid"))
async def my_id(message: types.Message):
    await message.answer(f"Ваш Telegram ID:\n{message.from_user.id}")


@dp.message(Command("generate_pins"))
async def generate_pins(message: types.Message):
    if not ADMIN_ID or str(message.from_user.id) != str(ADMIN_ID):
        await message.answer("У вас немає доступу до цієї команди.")
        return

    pins = set()

    while len(pins) < 3000:
        pins.add(generate_pin())

    async with db_pool.acquire() as conn:
        for pin in pins:
            await conn.execute(
                "INSERT INTO pins (code) VALUES ($1) ON CONFLICT (code) DO NOTHING",
                pin
            )

    text = "\n".join(sorted(pins))
    file = BufferedInputFile(
        text.encode("utf-8"),
        filename="pins.txt"
    )

    await message.answer_document(
        document=file,
        caption="Готово ✅ Створено 3000 одноразових PIN-кодів."
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id

    if await is_user_activated(user_id):
        await message.answer(
            "Ви вже активовані ✅\nОберіть матеріал:",
            reply_markup=lessons_keyboard()
        )
    else:
        await message.answer("Введіть ваш одноразовий PIN-код для активації доступу:")


@dp.message()
async def check_pin(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    pin = message.text.strip()

    if await is_user_activated(user_id):
        await message.answer(
            "Ваш доступ вже активований ✅\nОберіть матеріал:",
            reply_markup=lessons_keyboard()
        )
        return

    result = await activate_user_with_pin(user_id, username, pin)

    if result == "activated":
        await message.answer(
            "Активація успішна ✅\nВаш доступ збережено. Тепер оберіть матеріал:",
            reply_markup=lessons_keyboard()
        )
    elif result == "used":
        await message.answer("Цей PIN-код вже використаний. Введіть інший код.")
    else:
        await message.answer("Невірний PIN-код. Перевірте код і спробуйте ще раз.")


@dp.callback_query()
async def send_lesson(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await is_user_activated(user_id):
        await callback.message.answer("Спочатку активуйте доступ через /start")
        await callback.answer()
        return

    lesson = LESSONS.get(callback.data)

    if not lesson:
        await callback.answer("Матеріал не знайдено")
        return

    for file_id in lesson["files"]:
        await callback.message.answer_video(video=file_id)

    await callback.answer()


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN не знайдено.")

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не знайдено.")

    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
