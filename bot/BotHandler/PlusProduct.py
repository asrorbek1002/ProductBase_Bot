from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, CommandHandler, ConversationHandler
from asgiref.sync import sync_to_async
from django.db import transaction
from bot.models import Product, Warehouse, Transaction, Category

CATEGORY_SELECT, PRODUCT_SELECT, QUANTITY_SELECT = range(3)

def back_main_menu_buttons():
    return [[InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel")]]

async def plus_product(update: Update, context):
    categories = await sync_to_async(list)(Category.objects.all())
    keyboard = []
    row = []
    
    for i, cat in enumerate(categories, start=1):
        row.append(InlineKeyboardButton(f"{cat.name} ({await sync_to_async(Product.objects.filter(category=cat).count)()})", callback_data=f"xbazepiluscategory_{cat.id}"))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard += back_main_menu_buttons()
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Kategoriyani tanlang:", reply_markup=reply_markup)

async def category_selected(update: Update, context):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split('_')[1])

    products = await sync_to_async(list)(Product.objects.filter(category_id=category_id))
    keyboard = []
    row = []
    
    for i, prod in enumerate(products, start=1):
        quantity = await sync_to_async(lambda: Warehouse.objects.filter(product=prod).values_list("quantity", flat=True).first() or 0)()
        row.append(InlineKeyboardButton(f"{prod.name} ({quantity})", callback_data=f"qbazepilusproduct_{prod.id}"))
        if i % 4 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard += back_main_menu_buttons()
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Mahsulotni tanlang:", reply_markup=reply_markup)

async def product_selected(update: Update, context):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split('_')[1])
    context.user_data['product_id'] = product_id

    reply_markup = InlineKeyboardMarkup(back_main_menu_buttons())
    await query.edit_message_text("Nechta qo'shmoqchisiz? (son kiriting)", reply_markup=reply_markup)
    
    return "QUANTITY_SELECT"

async def quantity_received(update: Update, context):
    quantity = int(update.message.text)
    product_id = context.user_data['product_id']
    product = await sync_to_async(Product.objects.get)(id=product_id)
    
    @sync_to_async
    def save_transaction():
        with transaction.atomic():
            warehouse, _ = Warehouse.objects.get_or_create(product=product)
            warehouse.quantity += quantity
            warehouse.save()
            return Transaction.objects.create(product=product, transaction_type='in', quantity=quantity)

    await save_transaction()
    await update.message.reply_text(f"{product.name} mahsulotidan {quantity} {product.unit} qo'shildi!")
    
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END



