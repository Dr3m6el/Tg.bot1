from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import json
from telegram import ReplyKeyboardMarkup
# Загрузка приветственного сообщения
def load_welcome():
    with open("welcome.json", "r", encoding="utf-8") as f:
        return json.load(f)

WELCOME_CONTENT = load_welcome()

# Загрузка FAQ
def load_faq():
    with open("faq.json", "r", encoding="utf-8") as f:
        return json.load(f)

FAQ_QUESTIONS = load_faq()

def get_main_reply_keyboard():
    return ReplyKeyboardMarkup(
        [["🏠 Главное меню"]],
        resize_keyboard=True
    )

def get_support_keyboard():
    return ReplyKeyboardMarkup(
        [["❌ Завершить чат"]],
        resize_keyboard=True
    )


MAIN_INLINE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("❓ Частые вопросы", callback_data="faq")],
    [InlineKeyboardButton("✍ Задать вопрос", callback_data="ask_question")],
    [InlineKeyboardButton("ℹ️ О боте", callback_data="about")],
    [InlineKeyboardButton("🛠 Техподдержка", callback_data="support")]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if WELCOME_CONTENT.get("image_path"):
        if WELCOME_CONTENT["image_path"].startswith("http"):
            await update.message.reply_photo(photo=WELCOME_CONTENT["image_path"])
        else:
            with open(WELCOME_CONTENT["image_path"], "rb") as photo:
                await update.message.reply_photo(photo=photo)

    await update.message.reply_text(
        WELCOME_CONTENT.get("text", "Добро пожаловать!"),
        parse_mode="Markdown",
        reply_markup=MAIN_INLINE_KEYBOARD
    )
    await update.message.reply_text("Вы можете использовать кнопки ниже:", reply_markup=get_main_reply_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Напиши свой вопрос, и я постараюсь помочь.")
