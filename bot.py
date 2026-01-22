import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
from threading import Thread

# ================== CONFIG ==================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPER_ADMIN_ID = 1982275762

MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"
ADMINS_FILE = "admins.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ================== FILE HELPERS ==================
def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f:
            json.dump(default, f)
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_movies():
    return load_json(MOVIES_FILE, {})

def load_users():
    return load_json(USERS_FILE, {})

def load_admins():
    admins = load_json(ADMINS_FILE, [SUPER_ADMIN_ID])
    if SUPER_ADMIN_ID not in admins:
        admins.append(SUPER_ADMIN_ID)
    save_json(ADMINS_FILE, admins)
    return admins

def is_admin(user_id):
    return user_id in load_admins()

# ================== USER TRACKING ==================
def track_user(message):
    users = load_users()
    uid = str(message.from_user.id)
    now = datetime.now().isoformat()

    if uid not in users:
        users[uid] = {
            "first_seen": now,
            "last_active": now
        }
    else:
        users[uid]["last_active"] = now

    save_json(USERS_FILE, users)

# ================== MENUS ==================
def admin_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👥 Userlar", "🎬 Kinolar")
    kb.row("🛡 Adminlar", "⬅️ Chiqish")
    return kb

def movies_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Kino qo‘shish", "🗑 Kino o‘chirish")
    kb.row("⬅️ Orqaga")
    return kb

def admins_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Admin qo‘shish", "➖ Adminni o‘chirish")
    kb.row("⬅️ Orqaga")
    return kb

# ================== STATES ==================
state = {}

# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):
    track_user(message)
    bot.send_message(
        message.chat.id,
        "🎬 <b>Kodli Kino Olami</b>\n\nKino kodini yuboring (masalan: 101)"
    )

# ================== ADMIN PANEL ==================
@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(
        message.chat.id,
        "🔐 <b>Admin Panel</b>",
        reply_markup=admin_main_menu()
    )

# ================== USER STATS ==================
@bot.message_handler(func=lambda m: m.text == "👥 Userlar")
def users_stats(message):
    if not is_admin(message.from_user.id):
        return

    users = load_users()
    now = datetime.now()
    month_ago = now - timedelta(days=30)

    total = len(users)
    active = 0

    for u in users.values():
        last = datetime.fromisoformat(u["last_active"])
        if last >= month_ago:
            active += 1

    inactive = total - active

    bot.send_message(
        message.chat.id,
        f"📊 <b>Foydalanuvchilar statistikasi</b>\n\n"
        f"👥 Jami: <b>{total}</b>\n"
        f"✅ Faol (30 kun): <b>{active}</b>\n"
        f"❌ Nofaol: <b>{inactive}</b>"
    )

# ================== MOVIES PANEL ==================
@bot.message_handler(func=lambda m: m.text == "🎬 Kinolar")
def movies_panel(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(
        message.chat.id,
        "🎬 <b>Kinolar boshqaruvi</b>",
        reply_markup=movies_menu()
    )

@bot.message_handler(func=lambda m: m.text == "➕ Kino qo‘shish")
def add_movie_start(message):
    if not is_admin(message.from_user.id):
        return
    state[message.chat.id] = {"step": "movie_code"}
    bot.send_message(message.chat.id, "🔢 Kino kodini yuboring:")

@bot.message_handler(func=lambda m: m.text == "🗑 Kino o‘chirish")
def delete_movie_start(message):
    if not is_admin(message.from_user.id):
        return
    state[message.chat.id] = {"step": "delete_movie"}
    bot.send_message(message.chat.id, "🔢 O‘chiriladigan kino kodini yuboring:")

# ================== ADMINS PANEL ==================
@bot.message_handler(func=lambda m: m.text == "🛡 Adminlar")
def admins_panel(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(
        message.chat.id,
        "🛡 <b>Adminlar boshqaruvi</b>",
        reply_markup=admins_menu()
    )

@bot.message_handler(func=lambda m: m.text == "➕ Admin qo‘shish")
def add_admin_start(message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    state[message.chat.id] = {"step": "add_admin"}
    bot.send_message(message.chat.id, "🆔 Admin qilinadigan Telegram ID ni yuboring:")

@bot.message_handler(func=lambda m: m.text == "➖ Adminni o‘chirish")
def remove_admin_start(message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    admins = load_admins()
    text = "🛡 Hozirgi adminlar:\n\n"
    for a in admins:
        text += f"- {a}\n"
    text += "\n🆔 O‘chiriladigan admin ID ni yuboring:"
    state[message.chat.id] = {"step": "remove_admin"}
    bot.send_message(message.chat.id, text)

# ================== BACK ==================
@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def go_back(message):
    if is_admin(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🔐 Admin panel",
            reply_markup=admin_main_menu()
        )
    else:
        bot.send_message(
            message.chat.id,
            "🎬 Kino kodini yuboring",
            reply_markup=types.ReplyKeyboardRemove()
        )

@bot.message_handler(func=lambda m: m.text == "⬅️ Chiqish")
def exit_admin(message):
    bot.send_message(
        message.chat.id,
        "🎬 Kino kodini yuboring",
        reply_markup=types.ReplyKeyboardRemove()
    )

# ================== STATE HANDLER ==================
@bot.message_handler(content_types=["text", "video", "document"])
def handle_states(message):
    track_user(message)
    chat_id = message.chat.id

    if chat_id not in state:
        # oddiy kino kodi
        if message.text and message.text.isdigit():
            movies = load_movies()
            code = message.text
            if code in movies:
                m = movies[code]
                if m["type"] == "text":
                    bot.send_message(chat_id, m["data"])
                elif m["type"] == "video":
                    bot.send_video(chat_id, m["data"])
                elif m["type"] == "document":
                    bot.send_document(chat_id, m["data"])
            else:
                bot.send_message(chat_id, "❌ Bunday kino topilmadi")
        return

    step = state[chat_id]["step"]

    # ===== ADD MOVIE =====
    if step == "movie_code":
        state[chat_id] = {"step": "movie_content", "code": message.text}
        bot.send_message(chat_id, "📥 Endi kinoni yuboring (link / video / fayl):")
        return

    if step == "movie_content":
        code = state[chat_id]["code"]
        movies = load_movies()

        if message.content_type == "text":
            movies[code] = {"type": "text", "data": message.text}
        elif message.content_type == "video":
            movies[code] = {"type": "video", "data": message.video.file_id}
        elif message.content_type == "document":
            movies[code] = {"type": "document", "data": message.document.file_id}

        save_json(MOVIES_FILE, movies)
        state.pop(chat_id)
        bot.send_message(chat_id, "✅ Kino qo‘shildi")
        return

    # ===== DELETE MOVIE =====
    if step == "delete_movie":
        movies = load_movies()
        code = message.text
        if code in movies:
            del movies[code]
            save_json(MOVIES_FILE, movies)
            bot.send_message(chat_id, "🗑 Kino o‘chirildi")
        else:
            bot.send_message(chat_id, "❌ Bunday kod yo‘q")
        state.pop(chat_id)
        return

    # ===== ADD ADMIN =====
    if step == "add_admin":
        admins = load_admins()
        new_id = int(message.text)
        if new_id not in admins:
            admins.append(new_id)
            save_json(ADMINS_FILE, admins)
            bot.send_message(chat_id, "✅ Admin qo‘shildi")
        else:
            bot.send_message(chat_id, "⚠️ Bu foydalanuvchi allaqachon admin")
        state.pop(chat_id)
        return

    # ===== REMOVE ADMIN =====
    if step == "remove_admin":
        admins = load_admins()
        rem_id = int(message.text)
        if rem_id == SUPER_ADMIN_ID:
            bot.send_message(chat_id, "❌ Super adminni o‘chirish mumkin emas")
        elif rem_id in admins:
            admins.remove(rem_id)
            save_json(ADMINS_FILE, admins)
            bot.send_message(chat_id, "🗑 Adminlik olib tashlandi")
        else:
            bot.send_message(chat_id, "❌ Bu ID admin emas")
        state.pop(chat_id)
        return

# ================== RUN ==================
bot.infinity_polling()
