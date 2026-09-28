import os
import asyncio
import asyncpg
import secrets
import string

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    BufferedInputFile,
)


TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_ID = os.getenv("ADMIN_ID")


# Три нові частини + збережений подкаст із юристом.
# Для кожного матеріалу окремо вказані Telegram file_id відео та PDF.
LESSONS = {
    "lesson_1": {
        "title": "Частина 1",
        "style": "primary",
        "video": "BAACAgIAAxkBAANnarqES0aFgGjVqBP2rqoVhojHzgsAAv2xAAJngNhJJZ1VvfueLjo9BA",
        "pdf": "BQACAgIAAxkBAANtarqE5Ix0gTGi94-IV358jBfig1cAAgGyAAJngNhJXf2y_oT681A9BA",
    },
    "lesson_2": {
        "title": "Частина 2",
        "style": "primary",
        "video": "BAACAgIAAxkBAANparqEgIkYemrc_ebg4aFYwLExcB8AAv-xAAJngNhJwzuzfa8Tgkg9BA",
        "pdf": "BQACAgIAAxkBAANvarqE7L8KpjzE4wkTfc291df15sYAAgKyAAJngNhJ4Qthe1xGKv49BA",
    },
    "lesson_3": {
        "title": "Частина 3",
        "style": "primary",
        "video": "BAACAgIAAxkBAANrarqE0QhSOYRVSuYYH6fMDNmOMfsAA7IAAmeA2EnUMyz9b1wQLT0E",
        "pdf": "BQACAgIAAxkBAANxarqE9J10mM0VD0sdf_mKOgYfW88AAgOyAAJngNhJgIgfH_MUne89BA",
    },
    "lawyer_podcast": {
        "title": "Подкаст з юристом",
        "style": "success",
        "video": "BAACAgIAAyEFAATi_-lbAAMVaghAGdmQ8qlSozeLkqn9gV5_Y8UAAkelAAKp9IlLShFmtja0j3A7BA",
        "pdf": "BQACAgIAAyEFAATi_-lbAAMXaghAghVRJdqWl-qJ2yTn6mjBYDoAAg2dAAIbZElI1COFJhYDm1k7BA",
    },
}


bot = Bot(token=TOKEN)
dp = Dispatcher()
db_pool = None


def is_admin(user_id: int) -> bool:
    return bool(ADMIN_ID) and str(user_id) == str(ADMIN_ID)


def lessons_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=data["title"],
                    callback_data=key,
                    style=data.get("style"),
                )
            ]
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
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pins (
                code TEXT PRIMARY KEY,
                used_by BIGINT,
                used_username TEXT,
                used_at TIMESTAMP
            );
            """
        )

        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activated_users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                activated_at TIMESTAMP DEFAULT NOW()
            );
            """
        )


async def is_user_activated(user_id: int) -> bool:
    async with db_pool.acquire() as conn:
        result = await conn.fetchval(
            "SELECT user_id FROM activated_users WHERE user_id = $1", user_id
        )
        return result is not None


async def activate_user_with_pin(user_id: int, username: str, pin: str) -> str:
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            code = await conn.fetchrow(
                "SELECT code, used_by FROM pins WHERE code = $1 FOR UPDATE", pin
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
                pin,
            )

            await conn.execute(
                """
                INSERT INTO activated_users (user_id, username)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO NOTHING
                """,
                user_id,
                username,
            )

            return "activated"


@dp.message(Command("myid"))
async def my_id(message: types.Message):
    await message.answer(f"Ваш Telegram ID:\n{message.from_user.id}")


@dp.message(Command("media_help"))
async def media_help(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас немає доступу до цієї команди.")
        return

    await message.answer(
        "Надішліть мені відео або PDF окремими повідомленнями.\n\n"
        "У відповідь я покажу Telegram file_id кожного файла. "
        "Потім ці значення можна вставити в уроки бота."
    )


# Ці обробники обов'язково мають стояти вище за загальний check_pin.
@dp.message(F.video)
async def get_video_file_id(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Надсилати навчальні матеріали може лише адміністратор.")
        return

    video = message.video
    size_mb = (video.file_size or 0) / 1024 / 1024
    await message.answer(
        "🎬 VIDEO_FILE_ID\n\n"
        f"<code>{video.file_id}</code>\n\n"
        f"Розмір: {size_mb:.1f} МБ",
        parse_mode="HTML",
    )


@dp.message(F.document)
async def get_document_file_id(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Надсилати навчальні матеріали може лише адміністратор.")
        return

    document = message.document
    if document.mime_type != "application/pdf":
        await message.answer("Надішліть документ саме у форматі PDF.")
        return

    size_mb = (document.file_size or 0) / 1024 / 1024
    await message.answer(
        "📄 PDF_FILE_ID\n\n"
        f"<code>{document.file_id}</code>\n\n"
        f"Файл: {document.file_name or 'без назви'}\n"
        f"Розмір: {size_mb:.1f} МБ",
        parse_mode="HTML",
    )


@dp.message(Command("generate_pins"))
async def generate_pins(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас немає доступу до цієї команди.")
        return

    pins = set()

    while len(pins) < 1000:
        pins.add(generate_pin())

    async with db_pool.acquire() as conn:
        for pin in pins:
            await conn.execute(
                "INSERT INTO pins (code) VALUES ($1) ON CONFLICT (code) DO NOTHING",
                pin,
            )

    text = "\n".join(sorted(pins))
    file = BufferedInputFile(text.encode("utf-8"), filename="pins.txt")

    await message.answer_document(
        document=file,
        caption="Готово ✅ Створено 1000 одноразових PIN-кодів.",
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id

    if await is_user_activated(user_id):
        await message.answer(
            "Ви вже активовані ✅\nОберіть матеріал:",
            reply_markup=lessons_keyboard(),
        )
    else:
        await message.answer(
            "Введіть ваш одноразовий PIN-код для активації доступу:"
        )


@dp.message()
async def check_pin(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    # Не намагаємося викликати .strip() у відео, фото, стікерів тощо.
    if not message.text:
        await message.answer("Введіть PIN-код текстовим повідомленням.")
        return

    pin = message.text.strip()

    if await is_user_activated(user_id):
        await message.answer(
            "Ваш доступ вже активований ✅\nОберіть матеріал:",
            reply_markup=lessons_keyboard(),
        )
        return

    result = await activate_user_with_pin(user_id, username, pin)

    if result == "activated":
        await message.answer(
            "Активація успішна ✅\nВаш доступ збережено. "
            "Тепер оберіть матеріал:",
            reply_markup=lessons_keyboard(),
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

    await callback.message.answer_video(
        video=lesson["video"],
        caption=f"🎬 {lesson['title']}",
        protect_content=True,
    )

    await callback.message.answer_document(
        document=lesson["pdf"],
        caption=f"📄 Конспект — {lesson['title']}",
        protect_content=True,
    )

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
