import os
import asyncio
import asyncpg
import secrets
import string

DATABASE_URL = os.getenv("DATABASE_URL")
COUNT = 3000


def generate_pin(length=10):
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def main():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL не знайдено.")

    conn = await asyncpg.connect(DATABASE_URL)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS pins (
            code TEXT PRIMARY KEY,
            used_by BIGINT,
            used_username TEXT,
            used_at TIMESTAMP
        );
    """)

    pins = set()

    while len(pins) < COUNT:
        pins.add(generate_pin())

    for pin in pins:
        await conn.execute(
            "INSERT INTO pins (code) VALUES ($1) ON CONFLICT (code) DO NOTHING",
            pin
        )

    with open("pins.txt", "w", encoding="utf-8") as file:
        for pin in sorted(pins):
            file.write(pin + "\n")

    await conn.close()

    print(f"Готово. Створено {len(pins)} PIN-кодів.")
    print("Коди збережені у файлі pins.txt")


asyncio.run(main())
