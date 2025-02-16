from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from django.core.exceptions import ObjectDoesNotExist
from bot.models import Category, Product, Warehouse
from asgiref.sync import sync_to_async
from bot.utils import save_transaction_async


# Conversation states
NAME, PURCHASE_PRICE, SELLING_PRICE, UNIT, CATEGORY, QUANTITY = range(6)

# Unit choices
UNIT_CHOICES = [
    ('dona', 'Dona'),
    ('litr', 'Litr'),
    ('kg', 'Kilogram'),
    ('block', 'Block'),
]

def back_main_menu_buttons():
    return [[
        InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")
    ]]
async def start_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = await sync_to_async(list)(Category.objects.all())
    if not categories:
        await update.callback_query.edit_message_text("Hali kategoriyalar mavjud emas. Mahsulot qo'shishdan avval kategoriya qo'shganingiz maqul ☺️")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton(cat.name, callback_data=str(cat.id))] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard + back_main_menu_buttons())
    
    await update.callback_query.edit_message_text("Kategoriya tanlang:", reply_markup=reply_markup)
    return CATEGORY

async def product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        category = await sync_to_async(Category.objects.get)(id=int(query.data))
        context.user_data['category'] = category
    except ObjectDoesNotExist:
        await query.message.reply_text("Kategoriyani topib bo'lmadi. Qayta urinib ko'ring.")
        return CATEGORY
    
    await query.message.reply_text("Mahsulot nomini kiriting:", reply_markup=InlineKeyboardMarkup(back_main_menu_buttons()))
    return NAME

async def product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    
    keyboard = [[InlineKeyboardButton(name, callback_data=code)] for code, name in UNIT_CHOICES]
    reply_markup = InlineKeyboardMarkup(keyboard + back_main_menu_buttons())
    
    await context.bot.send_message(chat_id=update.effective_user.id, text="Mahsulot o‘lchov birligini tanlang:", reply_markup=reply_markup)
    return UNIT

async def product_unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['unit'] = query.data
    
    await query.message.reply_text("Mahsulot miqdorini kiriting:", reply_markup=InlineKeyboardMarkup(back_main_menu_buttons()))
    return QUANTITY

async def product_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['quantity'] = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Iltimos, miqdorni to'g'ri kiriting:")
        return QUANTITY
    
    await update.message.reply_text("Mahsulot sotib olingan narxini kiriting:", reply_markup=InlineKeyboardMarkup(back_main_menu_buttons()))
    return PURCHASE_PRICE

async def product_purchase_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['purchase_price'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Iltimos, to'g'ri narx kiriting:")
        return PURCHASE_PRICE
    
    await update.message.reply_text("Mahsulot sotish narxini kiriting:", reply_markup=InlineKeyboardMarkup(back_main_menu_buttons()))
    return SELLING_PRICE

async def product_selling_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data['selling_price'] = float(update.message.text)
    except ValueError:
        await update.message.reply_text("Iltimos, to'g'ri narx kiriting:")
        return SELLING_PRICE
    
    product = Product(
        name=context.user_data['name'],
        purchase_price=context.user_data['purchase_price'],
        selling_price=context.user_data['selling_price'],
        unit=context.user_data['unit'],
        category=context.user_data['category']
    )
    await sync_to_async(product.save)()
    
    warehouse = Warehouse(
        product=product,
        quantity=context.user_data['quantity']
    )
    await sync_to_async(warehouse.save)()
    
    await save_transaction_async(product, "in", warehouse.quantity)
    
    await update.message.reply_text(
        f"<blockquote>Mahsulot qo'shildi 🎉</blockquote>\n\n"
        f"📌 <b>Nomi:</b> {product.name}\n"
        f"💰 <b>Sotib olish narxi:</b> {product.purchase_price} so'm\n"
        f"💵 <b>Sotish narxi:</b> {product.selling_price} so'm\n"
        f"📦 <b>Miqdori: </b>{warehouse.quantity} {product.unit}\n"
        f"📂 <b>Kategoriya:</b> {product.category.name}",
        parse_mode="HTML"
    )
    return ConversationHandler.END


admins_keyboard = [
    [
        InlineKeyboardButton(text="📊 Do'kon statistikasi", callback_data='Stats_Shop')
    ],
    [
        InlineKeyboardButton(text="➕ Omborga tovar qo'shish", callback_data='PILUS_PRODUCT'),
        InlineKeyboardButton(text="➖ Ombordan tovar ayirish", callback_data='MINUS_PRODUCT')
    ],
    [
        InlineKeyboardButton(text="📦 Kategoriya qo'shish", callback_data="ADD_CATEGORY")
    ],
    [
        InlineKeyboardButton(text="🟩 Mahsulot qo'shish", callback_data='add_product_to_base'),
        InlineKeyboardButton(text="🟥 Mahsulot o'chirish", callback_data='delete_product_to_base')
    ],
    [
        InlineKeyboardButton(text="📄 Tovarlar ro'yxati", callback_data='lists_product')
    ]
]

admin_keyboard = InlineKeyboardMarkup(admins_keyboard)


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.edit_message_text("🏠 Asosiy menyu", reply_markup=admin_keyboard)
    return ConversationHandler.END

add_product_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add_product, pattern=r"^add_product_to_base$")],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_name)],
        PURCHASE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_purchase_price)],
        QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_quantity)],
        SELLING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_selling_price)],
        UNIT: [CallbackQueryHandler(product_unit)],
        CATEGORY: [CallbackQueryHandler(product_category)],
    },
    fallbacks=[CallbackQueryHandler(main_menu_handler, pattern="^main_menu$")]
)
