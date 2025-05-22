# support.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Активные сессии поддержки
active_support_sessions = set()

# Кому админ собирается ответить
admin_reply_context = {}

# ID администратора (укажи свой)
ADMIN_CHAT_ID = 123456789

# Основная клавиатура (если нужно использовать где-то ещё)
MAIN_INLINE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🛠 Техподдержка", callback_data="support")]
])

# --- Запуск поддержки пользователем ---
async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    active_support_sessions.add(user_id)

    context.user_data["awaiting_support"] = True

    await query.answer()
    await query.edit_message_text(
        "📞 Связаться с техподдержкой:\n\n"
        "📧 Email: support@agpk.edu\n"
        "📱 Telegram: @agpk_support\n\n"
        "✍️ Напишите сюда свой вопрос. Чтобы завершить — нажмите кнопку ниже.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Завершить чат", callback_data="user_end_support")]
        ])
    )

# --- Сообщения пользователя в поддержку ---
async def support_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if not context.user_data.get("awaiting_support"):
        return

    user = update.message.from_user
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"📨 Сообщение от @{user.username or user.first_name} (ID: {user_id}):\n{text}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✉️ Ответить", callback_data=f"admin_reply_to_{user_id}"),
                InlineKeyboardButton("✅ Завершить диалог", callback_data=f"admin_end_support_{user_id}")
            ]
        ])
    )
    await update.message.reply_text("✅ Ваше сообщение отправлено. Ожидайте ответа.")

# --- Обработка inline-кнопок ---
async def handle_support_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "user_end_support":
        active_support_sessions.discard(user_id)
        context.user_data["awaiting_support"] = False
        await query.edit_message_text("✅ Вы завершили чат с техподдержкой.")
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"🚫 Пользователь ID {user_id} завершил чат."
        )

    elif data.startswith("admin_end_support_"):
        try:
            target_user_id = int(data.rsplit("_", 1)[-1])
        except ValueError:
            await query.answer("❌ Ошибка в ID пользователя.", show_alert=True)
            return

        active_support_sessions.discard(target_user_id)
        await context.bot.send_message(
            chat_id=target_user_id,
            text="🔔 Техподдержка завершила диалог."
        )
        await query.edit_message_text("✅ Диалог завершён.")

    elif data.startswith("admin_reply_to_"):
        try:
            target_user_id = int(data.rsplit("_", 1)[-1])
        except ValueError:
            await query.answer("❌ Ошибка ID.", show_alert=True)
            return

        admin_reply_context[user_id] = target_user_id
        await query.edit_message_text(f"✉️ Напишите сообщение, чтобы отправить его пользователю (ID: {target_user_id}).")

# --- Сообщения ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if user_id == ADMIN_CHAT_ID:
        if user_id in admin_reply_context:
            target_user_id = admin_reply_context.pop(user_id)
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"📉 Ответ от техподдержки:\n\n{text}"
            )
            await update.message.reply_text("✅ Ответ пользователю отправлен.")
            return

    if context.user_data.get("awaiting_support"):
        await support_message_handler(update, context)
        return


    # Пользователь пишет в поддержку
    if context.user_data.get("awaiting_support"):
        await support_message_handler(update, context)
