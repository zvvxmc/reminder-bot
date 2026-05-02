import asyncio
import logging
from datetime import datetime, time
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==========================================
# НАСТРОЙКИ — ИЗМЕНИ ЭТО!
# ==========================================
BOT_TOKEN = "8591989979:AAE13qRDJExAs5tNpb-P1javuV7MSj3H1ag"
TASK_TEXT = "⏰ Напоминание! Твоё задание на сегодня:\n\n📌 Тебе нужно надеть наколенники!!"
TIMEZONE = "Asia/Tashkent"  # Узбекистан (UTC+5)
# ==========================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

active_users: dict[int, bool] = {}


def stop_button():
    """Кнопка 'Надоел' под каждым сообщением."""
    keyboard = [[InlineKeyboardButton("😤 Надоел! Стоп", callback_data="stop")]]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    active_users[chat_id] = True

    await update.message.reply_text(
        "✅ Бот запущен!\n\n"
        "🕕 Каждый день с 6:00 до 7:00 по Ташкентскому времени\n"
        "🔔 Буду напоминать каждые 15 минут\n\n"
        "Нажми кнопку «Надоел» под любым сообщением чтобы остановить.",
        reply_markup=stop_button()
    )
    logger.info(f"User {chat_id} started reminders")


async def handle_stop_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки Надоел."""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    active_users[chat_id] = False

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(
        "🛑 Хорошо, больше не буду!\n"
        "Напиши /start чтобы включить снова."
    )
    logger.info(f"User {chat_id} stopped reminders via button")


async def send_reminders(app: Application):
    """Фоновая задача: каждые 15 минут с 6:00 до 6:59 по Ташкенту."""
    tz = pytz.timezone(TIMEZONE)

    while True:
        now = datetime.now(tz)
        current_time = now.time()

        reminder_start = time(6, 0)
        reminder_end = time(6, 59)

        if reminder_start <= current_time <= reminder_end:
            for chat_id, is_active in list(active_users.items()):
                if is_active:
                    try:
                        await app.bot.send_message(
                            chat_id=chat_id,
                            text=TASK_TEXT,
                            reply_markup=stop_button()
                        )
                        logger.info(f"Reminder sent to {chat_id}")
                    except Exception as e:
                        logger.error(f"Failed to send to {chat_id}: {e}")

            # Ждём 15 минут
            await asyncio.sleep(600)
        else:
            # Вне окна — проверяем каждую минуту
            await asyncio.sleep(60)


async def post_init(app: Application):
    asyncio.create_task(send_reminders(app))


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_stop_button, pattern="^stop$"))

    logger.info("Bot started. Polling...")
    app.run_polling()


if __name__ == "__main__":
    main()