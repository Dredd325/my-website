import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# --- Конфиг ---
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))

if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен")

# Домен Railway — вручную в Variables
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Хендлеры ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # Если домен есть — WebApp, если нет — просто текст
    if RAILWAY_URL and RAILWAY_URL not in ("localhost", ""):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🟦 Открыть Blox",
                web_app=WebAppInfo(url=f"https://{RAILWAY_URL}")
            )]
        ])
        await message.answer(
            "<b>🟦 Blox</b>\n\nТапай, зарабатывай, качай бусты.\n\n👇 Жми кнопку",
            parse_mode="HTML",
            reply_markup=kb
        )
    else:
        await message.answer(
            "<b>🟦 Blox бот запущен!</b>\n\n"
            "WebApp появится после настройки домена Railway.\n"
            "Добавь переменную RAILWAY_PUBLIC_DOMAIN в Variables.",
            parse_mode="HTML"
        )

@dp.message(Command("profile"))
async def profile_cmd(message: types.Message):
    uid = message.from_user.id
    uname = message.from_user.username or "анон"
    await message.answer(
        f"<b>👤 Профиль</b>\n\nID: <code>{uid}</code>\nUsername: @{uname}\nБлоксов: 0",
        parse_mode="HTML"
    )

# --- Сервер ТОЛЬКО для статики (HTML), без вебхука ---
async def handle_index(request):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        return web.Response(text=html, content_type="text/html")
    except FileNotFoundError:
        return web.Response(text="index.html не найден. Положи файл в корень.", status=404)

async def main():
    # Запускаем бота в polling (без вебхука)
    asyncio.create_task(dp.start_polling(bot))

    # Простой веб-сервер для HTML
    app = web.Application()
    app.router.add_get("/", handle_index)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    logging.info(f"Сервер на порту {PORT}")
    logging.info(f"Polling запущен")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())