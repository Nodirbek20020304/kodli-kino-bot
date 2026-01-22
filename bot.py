import telebot
import json

TOKEN = "8563084277:AAEA7RpAxB4_V06X5VxBqzbeDOPVZvH7vq8"
ADMIN_ID = 1982275762

bot = telebot.TeleBot(TOKEN)

def load_movies():
    with open("movies.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_movies(data):
    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎬 Kodli Kino Olami\n\n"
        "Kino kodini yuboring (masalan: 101)"
    )

@bot.message_handler(func=lambda m: m.text.isdigit())
def send_movie(message):
    movies = load_movies()
    code = message.text

    if code in movies:
        movie = movies[code]
        bot.send_message(
            message.chat.id,
            f"🎥 {movie['title']}\n📥 {movie['link']}"
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Bunday kino topilmadi"
        )

@bot.message_handler(func=lambda m: m.text.startswith("/add"))
def add_movie(message):
    if message.chat.id != ADMIN_ID:
        return

    try:
        _, code, title, link = message.text.split("|")
        movies = load_movies()
        movies[code] = {"title": title, "link": link}
        save_movies(movies)
        bot.send_message(message.chat.id, "✅ Kino qo‘shildi")
    except:
        bot.send_message(
            message.chat.id,
            "❌ Format:\n/add|103|Kino nomi|https://link"
        )

bot.infinity_polling()
