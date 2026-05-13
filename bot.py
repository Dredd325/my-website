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

# Пробуем получить домен Railway
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не установлен")

# Если домена нет (первый билд) — используем тестовый, потом обновим
if not RAILWAY_URL or RAILWAY_URL == "localhost":
    RAILWAY_URL = "ваш-домен.railway.app"  # ЗАМЕНИ НА СВОЙ ДОМЕН ИЗ RAILWAY

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{RAILWAY_URL}{WEBHOOK_PATH}"
WEBAPP_URL = f"https://{RAILWAY_URL}"

logging.basicConfig(level=logging.INFO)
logging.info(f"Railway URL: {RAILWAY_URL}")
logging.info(f"Webhook URL: {WEBHOOK_URL}")

# --- Бот ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ... остальной код без изменений ...