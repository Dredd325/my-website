import asyncio
import logging
import os
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# --- Config ---
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8000))
RAILWAY_URL = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost")
DB_FILE = "database.json"
ADMIN_IDS = [5203710686]  # ТВОЙ Telegram ID

logging.basicConfig(level=logging.INFO)

def load_db():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

db = load_db()

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name or "Anon"

    if user_id not in db["users"]:
        db["users"][user_id] = {
            "username": username,
            "balance": 0, "perTap": 1, "power": 30000, "maxPower": 30000,
            "powerCost": 10, "incomePerHour": 0, "level": 1, "totalEarned": 0,
            "assets": {}, "boosts": {}, "nickname": username, "lastSeen": 0
        }
        save_db(db)

    webapp_url = f"https://{RAILWAY_URL}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟦 Open Blox", web_app=WebAppInfo(url=webapp_url))]
    ])
    await message.answer(
        "<b>🟦 Blox</b>\n\nTap, earn, upgrade.\nYour progress is saved forever.",
        parse_mode="HTML",
        reply_markup=kb
    )

@dp.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Access denied.")
        return

    users = db["users"]
    top = sorted(users.items(), key=lambda x: x[1].get("balance", 0), reverse=True)[:10]

    text = "<b>⚙ Admin Panel</b>\n\n"
    text += f"<b>Total users:</b> {len(users)}\n"
    text += "<b>Top 10:</b>\n"
    for i, (uid, u) in enumerate(top, 1):
        text += f"  {i}. {u.get('nickname', '?')} — {u.get('balance', 0):,} BLOX (lvl {u.get('level', 1)})\n"

    text += "\n<b>Commands:</b>\n"
    text += "/admin — this panel\n"
    text += "/admin_set [user_id] [balance] — set balance\n"
    text += "/admin_del [user_id] — delete user\n"
    text += "/admin_clear — clear all users\n"

    await message.answer(text, parse_mode="HTML")

@dp.message(Command("admin_set"))
async def admin_set(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 3:
        await message.answer("Usage: /admin_set [user_id] [balance]")
        return
    uid, bal = args[1], int(args[2])
    if uid in db["users"]:
        db["users"][uid]["balance"] = bal
        save_db(db)
        await message.answer(f"✅ Balance for {uid} set to {bal:,}")
    else:
        await message.answer("User not found.")

@dp.message(Command("admin_del"))
async def admin_del(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /admin_del [user_id]")
        return
    uid = args[1]
    if uid in db["users"]:
        del db["users"][uid]
        save_db(db)
        await message.answer(f"✅ User {uid} deleted.")
    else:
        await message.answer("User not found.")

@dp.message(Command("admin_clear"))
async def admin_clear(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Access denied.")
        return
    db["users"] = {}
    save_db(db)
    await message.answer("✅ All users cleared. Database is empty.")

# --- API ---
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
            "username": u.get("nickname", u.get("username", "Anon")),
            "balance": u.get("balance", 0),
            "level": u.get("level", 1),
        })
    users.sort(key=lambda x: x["balance"], reverse=True)
    return web.json_response(users[:100])

async def handle_index(request):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    except:
        return web.Response(text="index.html not found", status=404)

async def main():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/user", api_get_user)
    app.router.add_post("/api/save", api_save_user)
    app.router.add_get("/api/top", api_top)

    asyncio.create_task(dp.start_polling(bot))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logging.info(f"Server on port {PORT}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())