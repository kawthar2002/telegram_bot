

import os
import json

import gspread
import random
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, JobQueue

# ---------- НАСТРОЙКИ ----------
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
sheet = client.open_by_key(GOOGLE_SHEET_KEY).get_worksheet(0)

# ---------- ПОДПИСЧИКИ ----------
subscribers = set()

# ---------- ФУНКЦИЯ ОТПРАВКИ КАРТОЧКИ ----------
async def send_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = sheet.get_all_records()  # обновляем данные перед отправкой
    row = random.choice(data)
    message = (
        "✨✨✨✨✨✨\n\n"  # пропуск строки после эмодзи
        f"💡 <b>{row.get('Word','')}</b>\n"
        "————\n"  # прямая линия после слова
        f"<i>{row.get('Sentence','')}</i>\n"
        f"🔹 Synonym: <b>{row.get('Synonym','')}</b>\n"
        f"🔸 Opposite: <b>{row.get('Opposite','')}</b>\n\n"  # пропуск строки после Opposite
        "✨✨✨✨✨✨"
    )
    await update.message.reply_text(message, parse_mode="HTML")
    subscribers.add(update.effective_chat.id)

# ---------- ФУНКЦИЯ ЕЖЕДНЕВНОЙ РАССЫЛКИ ----------
async def daily_broadcast(context: ContextTypes.DEFAULT_TYPE):
    data = sheet.get_all_records()  # обновляем данные перед рассылкой
    for chat_id in subscribers:
        row = random.choice(data)
        message = (
            "✨✨✨✨✨✨\n\n"
            f"💡 <b>{row.get('Word','')}</b>\n"
            "————\n"
            f"<i>{row.get('Sentence','')}</i>\n"
            f"🔹 Synonym: <b>{row.get('Synonym','')}</b>\n"
            f"🔸 Opposite: <b>{row.get('Opposite','')}</b>\n\n"
            "✨✨✨✨✨✨"
        )
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        except Exception as e:
            print(f"Не удалось отправить сообщение {chat_id}: {e}")

# ---------- ГЛАВНАЯ ФУНКЦИЯ ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), send_card))

    # ---------- JobQueue для ежедневной рассылки ----------
    job_queue: JobQueue = app.job_queue
    now = datetime.now()
    # Отправка в 12:00 каждый день
    first_run = now.replace(hour=12, minute=0, second=0, microsecond=0)
    if now >= first_run:
        first_run += timedelta(days=1)
    delay = (first_run - now).total_seconds()
    job_queue.run_repeating(daily_broadcast, interval=24*3600, first=delay)

    # Запуск бота
    print("Я НОВАЯ ВЕРСИЯ БОТА 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
