from telegram.ext import ContextTypes, ConversationHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from ..utils import save_user_to_db
from ..models import TelegramUser

from telegram import InlineKeyboardMarkup, InlineKeyboardButton


async def get_user_keyboard():
    """Bot uchun inline keyboardni dinamik yaratish."""
    # Asinxron holda guide ma’lumotini olish

    # Asosiy keyboard tugmalari
    users_keyboards = [
        [
            InlineKeyboardButton(text='💬 Adminga xabar yuborish', callback_data='Send_message_on_Admin'),
            InlineKeyboardButton(text="🔖 Do'kon haqida", callback_data='About_market')
        ]
    ]

    return InlineKeyboardMarkup(users_keyboards)


admins_keyboard = [
    [
        InlineKeyboardButton(text="📊 Do'kon statistikasi", callback_data='Stats_Shop')
    ],
    [
        InlineKeyboardButton(text="📥 Omborga tovar qo‘shish", callback_data='PILUS_PRODUCT'),
        InlineKeyboardButton(text="📤 Ombordan tovar ayirish", callback_data='MINUS_PRODUCT')
    ],
    [
        InlineKeyboardButton(text="📋 Tovarlar ro‘yxati", callback_data='lists_product')
    ],
    [
        InlineKeyboardButton(text="🟢 Mahsulot qo‘shish", callback_data='add_product_to_base'),
        InlineKeyboardButton(text="🔴 Mahsulot o‘chirish", callback_data='delete_product_to_base')
    ],
    [
        InlineKeyboardButton(text="📦 Kategoriya qo'shish", callback_data="ADD_CATEGORY")
    ]
]

admin_keyboard = InlineKeyboardMarkup(admins_keyboard)

async def testInlinehandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Botni ishga tushirish uchun komanda.
    """
    print(update.callback_query.data)
    data = update.effective_user
    if update.callback_query:
        await update.callback_query.answer("Asosiy menyu")
    await update.callback_query.delete_message()
    is_save = await save_user_to_db(data)
    admin_id = await TelegramUser.get_admin_ids()
    if update.effective_user.id in admin_id:
        await context.bot.send_message(chat_id=update.effective_user.id, text="<b>Asosiy menyu 🖥\n<tg-spoiler>/admin_panel</tg-spoiler></b>", reply_markup=admin_keyboard, parse_mode="html")
    else:
        reply_markup_user = await get_user_keyboard()
        await context.bot.send_message(chat_id=update.effective_user.id, text="<b>Assalomu alaykum 👋</b>", reply_markup=reply_markup_user, parse_mode="html") 
    return ConversationHandler.END
