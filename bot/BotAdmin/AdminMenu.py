from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import CallbackContext, ConversationHandler
from ..decorators import admin_required

admin_keyboard_list = [
    [
        InlineKeyboardButton(text="📨 Xabar yuborish", callback_data='send_messages'),
        InlineKeyboardButton(text="📊 Bot statistikasi", callback_data='botstats')
    ],
    [
        InlineKeyboardButton(text="👮‍♂️ Admin qo'shish", callback_data='add_admin'),
        InlineKeyboardButton(text="🙅‍♂️ Admin o'chirish", callback_data='delete_admin')
    ],
    [
        InlineKeyboardButton(text="🗒 Adminlar yo'yxati", callback_data="admin_list")
    ],
    [
        InlineKeyboardButton(text="⬇️ Bazani yuklash", callback_data='download_db')
    ]
]
Admin_keyboard = InlineKeyboardMarkup(admin_keyboard_list)

@admin_required
async def admin_menyu(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    await context.bot.send_message(
        chat_id=user_id, 
        text="<b>Salom Admin\nNima qilamiz bugun</b>", 
        parse_mode="HTML",
        reply_markup=Admin_keyboard
        )
    return ConversationHandler.END