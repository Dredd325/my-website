import asyncio
import logging
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# --- Конфиг ---
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
DB_FILE = "database.json"

logging.basicConfig(level=logging.INFO)

# --- База данных ---
def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f)

db = load_db()

# --- Бот ---
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name or "Анон"

    # Если юзер новый — создаём запись
    if user_id not in db["users"]:
        db["users"][user_id] = {
            "username": username,
            "balance": 0,
            "perTap": 1,
            "power": 30000,
            "maxPower": 30000,
            "powerCost": 10,
            "incomePerHour": 0,
            "level": 1,
            "totalEarned": 0,
            "assets": {},
            "boosts": {},
            "nickname": username,
        }
        save_db(db)

    webapp_url = f"https://{RAILWAY_URL}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟦 Открыть Blox", web_app=WebAppInfo(url=webapp_url))]
    ])
    await message.answer(
        "<b>🟦 Blox</b>\n\nТапай, зарабатывай, качай бусты.\nТвой прогресс сохранён навсегда.",
        parse_mode="HTML",
        reply_markup=kb
    )

# --- API эндпоинты ---
async def api_get_user(request):
    uid = request.query.get("uid", "")
    if uid in db["users"]:
        return web.json_response(db["users"][uid])
    return web.json_response({"error": "not found"}, status=404)

async def api_save_user(request):
    try:
        data = await request.json()
        uid = data.get("uid", "")
        if uid in db["users"]:
            db["users"][uid].update(data)
            save_db(db)
            return web.json_response({"status": "ok"})
        return web.json_response({"error": "not found"}, status=404)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)

async def api_top(request):
    users = []
    for uid, u in db["users"].items():
        users.append({
            "username": u.get("nickname", u.get("username", "Анон")),
            "balance": u.get("balance", 0),
            "level": u.get("level", 1),
        })
    users.sort(key=lambda x: x["balance"], reverse=True)
    return web.json_response(users[:100])

# --- Сервер ---
async def handle_index(request):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except:
        return web.Response(text="index.html не найден", status=404)

async def main():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/user", api_get_user)
    app.router.add_post("/api/save", api_save_user)
    app.router.add_get("/api/top", api_top)

    # Запускаем бота в polling
    asyncio.create_task(dp.start_polling(bot))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Сервер на порту {PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())