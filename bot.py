import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# --- Конфиг ---
TOKEN = os.getenv("BOT_TOKEN")
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")  # Railway сам выдаст

if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен")
if not RAILWAY_URL:
    # Если домен не задан — используем localhost для теста
    RAILWAY_URL = "localhost"

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{RAILWAY_URL}{WEBHOOK_PATH}"
WEBAPP_URL = f"https://{RAILWAY_URL}"

# --- Бот и диспетчер ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Хендлеры ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🟦 Открыть Blox",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])

    await message.answer(
        "<b>🟦 Blox</b>\n\n"
        "Тапай, зарабатывай Blox-блоксы, качай бусты, выполняй квесты.\n\n"
        "👇 Жми кнопку ниже и начни",
        parse_mode="HTML",
        reply_markup=kb
    )

@dp.message(Command("profile"))
async def profile_cmd(message: types.Message):
    uid = message.from_user.id
    uname = message.from_user.username or "анон"
    await message.answer(
        f"<b>👤 Твой профиль</b>\n\n"
        f"ID: <code>{uid}</code>\n"
        f"Username: @{uname}\n"
        f"Блоксов: <b>0</b>\n\n"
        f"ℹ️ Статистика появится в следующем обновлении",
        parse_mode="HTML"
    )

# --- aiohttp сервер ---
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

def main():
    logging.basicConfig(level=logging.INFO)

    # aiohttp приложение
    app = web.Application()

    # Webhook handler
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    # Старт / стоп
    app.on_startup.append(lambda _: on_startup(bot))
    app.on_shutdown.append(lambda _: on_shutdown(bot))

    # Раздаём статику (WebApp HTML)
    app.router.add_static("/", path="webapp", name="static")

    web.run_app(app, port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    main()