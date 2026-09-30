import os
import asyncio
import asyncpg
import secrets
import string
from datetime import datetime, timedelta, timezone

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

# Заповнюються у Railway після отримання кружечка та Zoom-посилання.
INTRO_VIDEO_NOTE_ID = os.getenv("INTRO_VIDEO_NOTE_ID", "")
REVIEW_DATE = os.getenv("REVIEW_DATE", "29.11")
REVIEW_TIME = os.getenv("REVIEW_TIME", "16:00")
REVIEW_START_AT = os.getenv("REVIEW_START_AT", "")
REVIEW_ZOOM_URL = os.getenv("REVIEW_ZOOM_URL", "")

FEEDBACK_CHAT_URL = "https://t.me/+_o1-2lmkNn4wMWYy"


INTRO_TEXT = """1️⃣

Привіт! Рада вітати вас у тренінгу <b>про етичну систему стабільних продажів</b> ✨

Попереду три частини, які допоможуть вам зібрати продажі в зрозумілу систему: навчитися продавати без тиску й маніпуляцій, побудувати стратегію під свою фінансову ціль та продумати шлях клієнта так, щоб продажі не залежали від випадковості чи одного вдалого запуску.

Матеріали відкриватимуться поступово, щоб ви могли не просто все переглянути, а спокійно пройти кожну частину, попрацювати з конспектом і виконати вправи.

А перед початком я хочу коротко розповісти, як краще працювати з тренінгом, щоб забрати з нього максимум."""


HOW_TO_TEXT = """3️⃣

<b>Як працювати з тренінгом:</b>

1. Тренінг складається з трьох частин, які відкриватимуться послідовно.
2. Спочатку перегляньте матеріал відповідної частини.
3. Після цього відкрийте файл із конспектом і воркбуком. Спочатку прочитайте конспект — він підготує вас до виконання вправи.
4. Дайте собі час на завдання. Тут немає «правильних» відповідей — важливо зафіксувати саме ваші думки й спостереження.
5. Коли завершите матеріал і вправу, натисніть «Готово, далі». Після цього бот відкриє наступну частину.

Раджу не переходити далі, поки ви не завершили попередню частину. Так у вас складеться цілісна картина, а робота не залишиться просто набором переглянутих матеріалів."""


LESSONS = {
    "lesson_1": {
        "title": "Частина 1. Етичні продажі",
        "video": "BAACAgIAAxkBAANnarqES0aFgGjVqBP2rqoVhojHzgsAAv2xAAJngNhJJZ1VvfueLjo9BA",
        "pdf": "BQACAgIAAxkBAAOIarqJWtIGX7hD-8Z9PPohS6MI6jMAAjKyAAJngNhJNtnUyW3_iEY9BA",
        "video_text": """4️⃣

<b>ЧАСТИНА 1. ЕТИЧНІ ПРОДАЖІ</b>

Починаємо з фундаменту: як продавати переконливо, але без тиску, маніпуляцій і внутрішнього відчуття, що ви комусь щось нав’язуєте.

У цій частині ми розберемо, де проходить межа між відповідальністю експерта та відповідальністю клієнта, як формується цінність продукту і на чому тримається етична комунікація.

<b>Таймкоди:</b>

00:00 — як працювати з тренінгом
04:42 — яку систему будемо будувати
07:19 — етичні та агресивні продажі
08:37 — концепція інтенсифікації
20:07 — соціально-етична модель і довіра
30:02 — потреби та психологія покупки
43:53 — етичний кодекс продажів
1:12:40 — чесні рамки продукту
1:30:41 — практичне завдання
1:33:39 — питання та додаткові приклади

Після перегляду обов’язково переходьте до конспекту — саме там ви зафіксуєте власну позицію у продажах.""",
        "workbook_text": """5️⃣

<b>КОНСПЕКТ І ВОРКБУК ДО ЧАСТИНИ 1</b>

У файлі відкрийте перший блок — від теми про соціально-етичні продажі до завдання <b>«Моя позиція в продажах»</b>.

Спочатку спокійно перечитайте конспект. Особливу увагу зверніть на етичний кодекс, межі відповідальності та чесні рамки продукту: кому він підходить, чого потребує від клієнта, що ви можете гарантувати, а що від вас не залежить.

Після цього виконайте вправу:

— за що відповідаєте ви;
— за що відповідає клієнт;
— що ви гарантуєте;
— чого не гарантуєте;
— коли припиняєте комунікацію;
— на якому принципі будується ваша система продажів.

У результаті у вас має з’явитися власна внутрішня опора, з якою буде легше говорити про продукт, тримати межі й не боятися самого моменту продажу.""",
    },
    "lesson_2": {
        "title": "Частина 2. Фундамент продажів",
        "video": "BAACAgIAAxkBAANparqEgIkYemrc_ebg4aFYwLExcB8AAv-xAAJngNhJwzuzfa8Tgkg9BA",
        "pdf": "BQACAgIAAxkBAAOJarqJWtoOyTjDwvLhkNgD3yHKgukAAjCyAAJngNhJTJ9VPQAB6U88PQQ",
        "video_text": """6️⃣

<b>ЧАСТИНА 2. ФУНДАМЕНТ ПРОДАЖІВ</b>

У цій частині розберемо, чому стабільний дохід починається не з більшої кількості дій, а з реалістичної фінансової цілі, правильної конфігурації ресурсів і зрозумілої стратегії.

<b>Таймкоди:</b>

00:00 — що формує фундамент стабільних продажів
08:25 — як поставити адекватну фінансову ціль
17:41 — практичне завдання для розрахунку цілі
19:40 — аудит ресурсів: аудиторія, бюджет і трафік
28:54 — співвідношення експертизи, чеку та часу
39:11 — стратегія продажів великими мазками
41:23 — позиціонування: хто я як експертка
46:37 — цільова аудиторія, сегменти й аватари
53:42 — як обрати, кому саме ви продаєте
1:00:48 — продукт як рішення, яке ви приносите на ринок
1:12:14 — межі експертності та відповідальна обіцянка
1:39:47 — три ключові відповіді, на яких тримається стратегія
1:41:44 — відповіді на запитання учасниць

Після перегляду переходьте до конспекту й практичної частини — там ви перекладете матеріал на свій проєкт.""",
        "workbook_text": """7️⃣

<b>КОНСПЕКТ І ВОРКБУК ДО ЧАСТИНИ 2</b>

Відкрийте блок <b>«Що таке фундамент продажів і від чого насправді залежить стабільність вашого доходу»</b>.

Спочатку прочитайте конспект, а потім послідовно виконайте три практичні блоки:

1. Розрахуйте фінансову ціль на наступний період і розкладіть її на кількість клієнтів, середній чек, формат продукту та час.
2. Проведіть аудит ресурсів: аудиторії, бюджету, трафіку, команди, експертизи, можливого чеку й часу на реалізацію.
3. Зберіть стратегію великими мазками: сформулюйте своє позиціонування, оберіть основний аватар клієнта та визначте рішення, яке ви приносите на ринок.

У результаті у вас має з’явитися не абстрактне «хочу більше заробляти», а зрозуміла опора: <b>скільки, для кого, за рахунок якого рішення та з якими ресурсами ви продаєте</b>.""",
    },
    "lesson_3": {
        "title": "Частина 3. Шлях клієнта",
        "video": "BAACAgIAAxkBAANrarqE0QhSOYRVSuYYH6fMDNmOMfsAA7IAAmeA2EnUMyz9b1wQLT0E",
        "pdf": "BQACAgIAAxkBAAOHarqJWnfA0q4E_2I2ncw8fEG_2L4AAjGyAAJngNhJAsU43Z2Cw249BA",
        "video_text": """8️⃣

<b>ЧАСТИНА 3. ШЛЯХ КЛІЄНТА</b>

У фінальній частині ми зберемо всі попередні напрацювання в систему: від першого контакту з людиною до заявки, продажу та наступних покупок.

<b>Таймкоди:</b>

00:00 — як спроєктувати шлях клієнта
06:26 — продуктова воронка та логіка продуктів
26:46 — як воронка створює стабільність доходу
35:14 — продукт-гачок і природний перехід далі
54:20 — траєкторія клієнта та паспорт продукту
57:59 — як зібрати скелет продукту
1:07:28 — ціноутворення й економіка продукту
1:24:37 — трансформація заявки в продаж
1:37:20 — трансформація перегляду в заявку
1:59:29 — генерація переглядів і лідів
2:01:23 — три типи аудиторії
2:08:11 — баланс аудиторій і відповідний контент
2:15:07 — як усі елементи складаються в систему
2:22:23 — відповіді на запитання учасниць

Після перегляду переходьте до воркбуку, щоб зібрати власний шлях клієнта — від першого дотику до повторної покупки.""",
        "workbook_text": """9️⃣

<b>КОНСПЕКТ І ВОРКБУК ДО ЧАСТИНИ 3</b>

Відкрийте блок <b>«Що таке шлях клієнта і як побудувати ланцюжок дій, який стабільно буде давати продажі з блогу?»</b>

Рухайтеся послідовно за п’ятьма кроками:

1. Зберіть траєкторію клієнта й логіку продуктової воронки.
2. Пропишіть продукт-гачок: точку А і Б, обіцянку, структуру, вигоди, формат продажу та ціну.
3. Оберіть модель продажів і створіть інструмент кваліфікації заявки.
4. Зберіть банк історій під чотири рівні недовіри: до ніші, вашої експертності, формату взаємодії та себе.
5. Визначте баланс широкої, середньої та швидко купуючої аудиторії. Підберіть для неї заголовки й логіку залучення.

Не намагайтеся заповнити все одним ривком. Ваш результат — <b>чіткий маршрут, яким людина проходить від першого контакту до покупки й наступного продукту</b>.""",
    },
}


LAWYER_PODCAST = {
    "video": "BAACAgIAAyEFAATi_-lbAAMVaghAGdmQ8qlSozeLkqn9gV5_Y8UAAkelAAKp9IlLShFmtja0j3A7BA",
    "pdf": "BQACAgIAAyEFAATi_-lbAAMXaghAghVRJdqWl-qJ2yTn6mjBYDoAAg2dAAIbZElI1COFJhYDm1k7BA",
}


FINISH_TEXT = f"""💭

Вітаю! Ви пройшли всі три частини тренінгу 🥳

Тепер у вас є можливість записатися на розбори, де ми вже зможемо попрацювати з питаннями, які залишилися після тренінгу, та тим, як усе це застосувати конкретно у вашій ситуації.

Щоб отримати доступ до запису на розбори, спочатку залиште, будь ласка, свій відгук про тренінг. Мені важливо зрозуміти не просто «сподобалось / не сподобалось», а що саме змінилося у вашому розумінні продажів після проходження.

Можете орієнтуватися на ці питання:

— З якою точкою А ви прийшли на тренінг? Що у продажах найбільше не виходило або було незрозумілим?
— Що змінилося у вашому розумінні продажів після трьох частин?
— Які інсайти або думки стали для вас найважливішими?
— Що ви вже змінили або плануєте змінити у своїй системі продажів після тренінгу?
— Чи отримали ви вже якийсь результат після впровадження матеріалів? Якщо так — який?
— Що найбільше сподобалося у самому тренінгу та форматі подачі?
— Кому б ви рекомендували цей тренінг і чому?

Залишити відгук можна в чаті тренінгу за посиланням:
{FEEDBACK_CHAT_URL}

Після того як залишите відгук, повертайтеся сюди та натискайте кнопку <b>«ХОЧУ НА РОЗБІР →»</b> — і я надішлю вам дати для реєстрації."""


bot = Bot(token=TOKEN)
dp = Dispatcher()
db_pool = None


def is_admin(user_id: int) -> bool:
    return bool(ADMIN_ID) and str(user_id) == str(ADMIN_ID)


def one_button(text: str, callback_data: str, *, green: bool = False):
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text=text,
                callback_data=callback_data,
                style="success" if green else None,
            )
        ]]
    )


def finish_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Залишити відгук", url=FEEDBACK_CHAT_URL)],
            [InlineKeyboardButton(
                text="ХОЧУ НА РОЗБІР →",
                callback_data="want_review",
                style="success",
            )],
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
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS review_registrations (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                review_date TEXT NOT NULL,
                review_time TEXT NOT NULL,
                registered_at TIMESTAMP DEFAULT NOW(),
                reminder_sent BOOLEAN DEFAULT FALSE
            );
        """)


async def is_user_activated(user_id: int) -> bool:
    async with db_pool.acquire() as conn:
        return await conn.fetchval(
            "SELECT user_id FROM activated_users WHERE user_id = $1", user_id
        ) is not None


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
                "UPDATE pins SET used_by=$1, used_username=$2, used_at=NOW() WHERE code=$3",
                user_id, username, pin,
            )
            await conn.execute(
                "INSERT INTO activated_users (user_id, username) VALUES ($1,$2) "
                "ON CONFLICT (user_id) DO NOTHING",
                user_id, username,
            )
            return "activated"


async def send_intro(message: types.Message):
    await message.answer(INTRO_TEXT, parse_mode="HTML")
    if INTRO_VIDEO_NOTE_ID:
        await message.answer_video_note(video_note=INTRO_VIDEO_NOTE_ID)
    await message.answer(
        HOW_TO_TEXT,
        parse_mode="HTML",
        reply_markup=one_button("ПЕРЕЙТИ ДО НАВЧАННЯ", "lesson_1"),
    )


async def send_lesson(message: types.Message, lesson_key: str):
    lesson = LESSONS[lesson_key]
    await message.answer_video(
        video=lesson["video"],
        caption=lesson["video_text"],
        parse_mode="HTML",
        supports_streaming=True,
        protect_content=True,
    )

    if lesson_key == "lesson_1":
        button = one_button("Готово, далі", "lesson_2", green=True)
    elif lesson_key == "lesson_2":
        button = one_button("Готово, далі", "lesson_3", green=True)
    else:
        button = one_button("Подкаст з юристом", "lawyer_podcast", green=True)

    await message.answer_document(
        document=lesson["pdf"],
        caption=lesson["workbook_text"],
        parse_mode="HTML",
        protect_content=True,
        reply_markup=button,
    )


async def send_lawyer_podcast(message: types.Message):
    await message.answer_video(
        video=LAWYER_PODCAST["video"],
        caption="🎬 Подкаст з юристом",
        protect_content=True,
    )
    await message.answer_document(
        document=LAWYER_PODCAST["pdf"],
        caption="📄 Матеріали до подкасту з юристом",
        protect_content=True,
        reply_markup=one_button(
            "Завершити тренінг →", "finish_training", green=True
        ),
    )


async def register_for_review(user_id: int, username: str) -> bool:
    async with db_pool.acquire() as conn:
        result = await conn.execute("""
            INSERT INTO review_registrations
                (user_id, username, review_date, review_time)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, username, REVIEW_DATE, REVIEW_TIME)
    return result == "INSERT 0 1"


async def reminder_loop():
    if not REVIEW_START_AT or not REVIEW_ZOOM_URL:
        return
    start_at = datetime.fromisoformat(REVIEW_START_AT)
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)
    reminder_at = start_at - timedelta(minutes=10)

    while True:
        now = datetime.now(timezone.utc)
        if reminder_at <= now <= start_at + timedelta(minutes=15):
            async with db_pool.acquire() as conn:
                users = await conn.fetch(
                    "SELECT user_id FROM review_registrations WHERE reminder_sent=FALSE"
                )
            for row in users:
                try:
                    await bot.send_message(
                        row["user_id"],
                        "Розбір починається через 10 хвилин 🤎\n\n"
                        f"Посилання на Zoom: {REVIEW_ZOOM_URL}",
                    )
                    async with db_pool.acquire() as conn:
                        await conn.execute(
                            "UPDATE review_registrations SET reminder_sent=TRUE WHERE user_id=$1",
                            row["user_id"],
                        )
                except Exception as error:
                    print(f"Не вдалося надіслати нагадування {row['user_id']}: {error}")
        await asyncio.sleep(30)


@dp.message(Command("myid"))
async def my_id(message: types.Message):
    await message.answer(f"Ваш Telegram ID:\n{message.from_user.id}")


@dp.message(Command("media_help"))
async def media_help(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("У вас немає доступу до цієї команди.")
        return
    await message.answer(
        "Надішліть мені відео, кружечок або PDF окремими повідомленнями.\n\n"
        "У відповідь я покажу Telegram file_id кожного файла."
    )


@dp.message(F.video_note)
async def get_video_note_file_id(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Надсилати матеріали може лише адміністратор.")
        return
    video_note = message.video_note
    size_mb = (video_note.file_size or 0) / 1024 / 1024
    await message.answer(
        "⭕ VIDEO_NOTE_FILE_ID\n\n"
        f"<code>{video_note.file_id}</code>\n\n"
        f"Розмір: {size_mb:.1f} МБ",
        parse_mode="HTML",
    )


@dp.message(F.video)
async def get_video_file_id(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("Надсилати матеріали може лише адміністратор.")
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
        await message.answer("Надсилати матеріали може лише адміністратор.")
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
    file = BufferedInputFile(
        "\n".join(sorted(pins)).encode("utf-8"), filename="pins.txt"
    )
    await message.answer_document(
        document=file,
        caption="Готово ✅ Створено 1000 одноразових PIN-кодів.",
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    if await is_user_activated(message.from_user.id):
        await send_intro(message)
    else:
        await message.answer("Введіть ваш одноразовий PIN-код для активації доступу:")


@dp.message()
async def check_pin(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    if not message.text:
        await message.answer("Введіть PIN-код текстовим повідомленням.")
        return
    if await is_user_activated(user_id):
        await message.answer(
            "Ваш доступ уже активований ✅\nНатисніть /start, щоб відкрити тренінг."
        )
        return

    result = await activate_user_with_pin(user_id, username, message.text.strip())
    if result == "activated":
        await message.answer("Активація успішна ✅ Ваш доступ збережено.")
        await send_intro(message)
    elif result == "used":
        await message.answer("Цей PIN-код вже використаний. Введіть інший код.")
    else:
        await message.answer("Невірний PIN-код. Перевірте код і спробуйте ще раз.")


@dp.callback_query()
async def handle_callback(callback: CallbackQuery):
    if not await is_user_activated(callback.from_user.id):
        await callback.answer(
            "Спочатку активуйте доступ через /start", show_alert=True
        )
        return

    action = callback.data
    await callback.answer()

    if action in LESSONS:
        await send_lesson(callback.message, action)
    elif action == "lawyer_podcast":
        await send_lawyer_podcast(callback.message)
    elif action == "finish_training":
        await callback.message.answer(
            FINISH_TEXT,
            parse_mode="HTML",
            reply_markup=finish_keyboard(),
        )
    elif action == "want_review":
        text = f"""🗓️

Тепер можна обрати дату розбору ✨

Розбори проходитимуть періодично, тому вам не обовʼязково записуватися саме на найближчий. Якщо ця дата вам не підходить — просто дочекайтеся наступної.

<b>Важливий момент:</b> у межах тренінгу ви можете записатися на розбір лише один раз.

Бот періодично повідомлятиме вам про нові дати розборів, тому не поспішайте реєструватися на першу запропоновану. Дочекайтеся тієї дати, яка вам <b>точно</b> буде зручною, і вже тоді підтверджуйте свою участь.

Щойно ви зареєструвалися на конкретну дату, ваша можливість запису вважається використаною. Якщо ви зареєструвалися, але не прийшли на розбір, повторно записатися вже не вийде.

<b>Актуальна дата найближчого розбору:</b>

📅 {REVIEW_DATE}
🕐 {REVIEW_TIME}

Якщо дата вам підходить — натискайте <b>«Так, я буду 🙋‍♀️»</b>. За 10 хвилин до початку бот надішле вам посилання на ефір."""
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=one_button(
                "Так, я буду 🙋‍♀️", "confirm_review", green=True
            ),
        )
    elif action == "confirm_review":
        created = await register_for_review(
            callback.from_user.id, callback.from_user.username or ""
        )
        if not created:
            await callback.message.answer(
                "Ви вже використали можливість запису на розбір."
            )
            return
        await callback.message.answer(
            "💭\n\nСупер, вас зареєстровано на розбір 🥳\n\n"
            f"Я додала вас до списку учасників на <b>{REVIEW_DATE} о {REVIEW_TIME}</b>. "
            "За 10 хвилин до початку розбору бот автоматично надішле вам "
            "посилання на Zoom. До зустрічі 🤎",
            parse_mode="HTML",
        )
    else:
        await callback.message.answer("Цей розділ поки недоступний.")


async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN не знайдено.")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не знайдено.")

    await init_db()
    reminder_task = asyncio.create_task(reminder_loop())
    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
