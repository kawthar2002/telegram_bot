

import os
import json
import random
import datetime
from datetime import timezone, timedelta

MOSCOW_TZ = timezone(timedelta(hours=3))

import gspread
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

from oauth2client.service_account import ServiceAccountCredentials

# ---------- CONFIG ----------
TOKEN = os.environ.get("BOT_TOKEN")
GOOGLE_SHEET_KEY = os.environ.get("SHEET_ID")
creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")

creds_dict = json.loads(creds_json)

# ---------- GOOGLE SHEETS ----------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(GOOGLE_SHEET_KEY).sheet1

# ---------- MEMORY ----------
subscribers = set()
user_times = {}   # chat_id -> "HH:MM"

# ---------- HELPERS ----------
def get_words():
    return sheet.get_all_records()

def pick_word():
    data = get_words()
    return random.choice(data) if data else None

def format_word(row):
    return (
        "✨✨✨✨✨✨\n\n"
        f"💡 <b>{row.get('Word','')}</b>\n"
        "————\n"
        f"<i>{row.get('Sentence','')}</i>\n"
        f"🔹 Synonym: <b>{row.get('Synonym','')}</b>\n"
        f"🔸 Opposite: <b>{row.get('Opposite','')}</b>\n\n"
        "✨✨✨✨✨✨"
    )

# ---------- ADD WORD ----------
async def add_word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = " ".join(context.args)
        parts = [p.strip() for p in text.split("|")]

        if len(parts) != 4:
            await update.message.reply_text(
                "Формат:\n/add word | sentence | synonym | opposite"
            )
            return

        sheet.append_row(parts)
        await update.message.reply_text("✅ Слово добавлено!")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# ---------- SET TIME ----------
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_str = context.args[0]  # HH:MM
        chat_id = update.effective_chat.id

        user_times[chat_id] = time_str
        subscribers.add(chat_id)

        await update.message.reply_text(f"⏰ Время установлено: {time_str}")

    except:
        await update.message.reply_text("Используй: /time 12:30")

# ---------- MESSAGE HANDLER ----------
async def send_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    word = pick_word()

    if not word:
        await update.message.reply_text("Слов пока нет.")
        return

    chat_id = update.effective_chat.id
    subscribers.add(chat_id)

    await update.message.reply_text(format_word(word), parse_mode="HTML")

# ---------- SCHEDULE CHECK ----------
async def check_schedule(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now(MOSCOW_TZ).strftime("%H:%M")

    data = get_words()
    if not data:
        return

    for chat_id, user_time in user_times.items():
        if user_time == now:
            word = random.choice(data)

            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=format_word(word),
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Error {chat_id}: {e}")

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("add", add_word))
    app.add_handler(CommandHandler("time", set_time))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), send_card))

    # scheduler (каждую минуту проверяем время)
    app.job_queue.run_repeating(check_schedule, interval=60, first=0)

    print("🚀 BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
    main()
