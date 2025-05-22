from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from handlers import start, help_command, get_main_reply_keyboard, MAIN_INLINE_KEYBOARD
from support import ADMIN_CHAT_ID, handle_support, support_message_handler, active_support_sessions, handle_support_buttons
# без admin_reply_handler

from dotenv import load_dotenv
import os
import httpx


# ---------- Загрузка переменных окружения ----------
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "qwen/qwen3-235b-a22b"

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❗ Не найден TELEGRAM_BOT_TOKEN в .env")
if not OPENROUTER_API_KEY:
    raise ValueError("❗ Не найден OPENROUTER_API_KEY в .env")

# ---------- ИИ обработчик ----------
async def ask_openrouter(question: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-Title": "TelegramBot"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Ты учебный помощник, отвечай понятно и кратко."},
            {"role": "user", "content": question}
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            content = await response.json()
            return content["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Ошибка OpenRouter:", e)
        return f"❗ Ошибка при обращении к ИИ: {e}"

# ---------- Обработка текстовых сообщений ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text.strip().lower()
    if user_msg == "🏠 главное меню":
        context.user_data["chat_with_ai"] = False
        await update.message.reply_text("🏠 Главное меню:", reply_markup=MAIN_INLINE_KEYBOARD)
        await update.message.reply_text("Вы можете использовать кнопки ниже:", reply_markup=get_main_reply_keyboard())
        return

    if context.user_data.get("awaiting_support"):
        await support_message_handler(update, context)
        return

    if context.user_data.get("chat_with_ai"):
        reply = await ask_openrouter(update.message.text)
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text("Выберите действие из меню ниже:", reply_markup=MAIN_INLINE_KEYBOARD)

# ---------- Обработка inline-кнопок ----------
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("end_support_"):
        try:
            user_id = int(data.split("_")[-1])
            active_support_sessions.discard(user_id)

            await context.bot.send_message(
                chat_id=user_id,
                text="🔔 Техподдержка завершила диалог. Если возникнут новые вопросы — напишите снова.",
                reply_markup=get_main_reply_keyboard()
            )

            await query.edit_message_text("✅ Диалог с пользователем завершён.")
        except Exception as e:
            print(f"[handle_button] Ошибка при завершении диалога: {e}")
            await query.edit_message_text("⚠️ Не удалось завершить диалог.")
        return

    if data == "faq":
        from handlers import FAQ_QUESTIONS
        faq_text = "\n\n".join([f"• *{q}*\n{a}" for q, a in FAQ_QUESTIONS.items()])
        await query.edit_message_text(f"❓ *Часто задаваемые вопросы:*\n\n{faq_text}", parse_mode="Markdown")

    elif data == "about":
        await query.edit_message_text("ℹ️ Бот помогает абитуриентам получить информацию о колледже.")

    elif data == "support":
        await query.edit_message_text("🔧 Подключение к техподдержке...")
        await handle_support(update, context)

    elif data == "ask_question":
        context.user_data["chat_with_ai"] = True
        await query.edit_message_text("🤖 Привет! Задай мне свой вопрос.")

    elif data == "main_menu":
        context.user_data["chat_with_ai"] = False
        await query.edit_message_text("🏠 Главное меню:", reply_markup=MAIN_INLINE_KEYBOARD)

# ---------- Обработка ошибок ----------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    import traceback
    print("Ошибка:", context.error)
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)

# ---------- Запуск приложения ----------
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Команды
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))

# Все остальные inline-кнопки
app.add_handler(CallbackQueryHandler(handle_button))

#Cообщения
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_support_buttons, pattern="^(user_end_support)$"))
app.add_handler(CallbackQueryHandler(handle_support_buttons, pattern="^(admin_reply_to_\\d+|admin_end_support_\\d+)$"))
app.add_handler(CallbackQueryHandler(handle_support, pattern="^support$"))

# Обработка ошибок
app.add_error_handler(error_handler)

print("🤖 Бот запущен с OpenRouter и техподдержкой")
app.run_polling()
 