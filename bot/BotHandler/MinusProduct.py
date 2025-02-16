from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler, MessageHandler, filters, CommandHandler, ConversationHandler
from asgiref.sync import sync_to_async
from django.db import transaction
from bot.models import Product, Warehouse, Transaction, Category


def back_main_menu_buttons():
    return [[InlineKeyboardButton("\u274c Bekor qilish", callback_data="main_menu")]]

async def minus_product(update: Update, context):
    categories = await sync_to_async(list)(Category.objects.all())
    keyboard = []
    row = []
    
    for i, cat in enumerate(categories, start=1):
        row.append(InlineKeyboardButton(f"{cat.name} ({await sync_to_async(Product.objects.filter(category=cat).count)()})", callback_data=f"category_{cat.id}"))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard += back_main_menu_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Kategoriyani tanlang:", reply_markup=reply_markup)
    return "MCATEGORY_SELECT"

async def category_selected(update: Update, context):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split('_')[1])

    products = await sync_to_async(list)(Product.objects.filter(category_id=category_id))
    keyboard = []
    row = []
    
    for i, prod in enumerate(products, start=1):
        quantity = await sync_to_async(lambda: Warehouse.objects.filter(product=prod).values_list("quantity", flat=True).first() or 0)()
        row.append(InlineKeyboardButton(f"{prod.name} ({quantity})", callback_data=f"minusproduct_{prod.id}"))
        if i % 4 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard += back_main_menu_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Mahsulotni tanlang:", reply_markup=reply_markup)
    return "MPRODUCT_SELECT"

async def product_selected(update: Update, context):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.split('_')[1])
    context.user_data['product_id'] = product_id
    reply_markup = InlineKeyboardMarkup(back_main_menu_buttons())
    await query.edit_message_text("Nechta kamaytirmoqchisiz? (son kiriting)", reply_markup=reply_markup)
    return "MQUANTITY_SELECT"

async def quantity_decrease(update: Update, context):
    try:
        quantity = int(update.message.text)
        product_id = context.user_data['product_id']
        product = await sync_to_async(Product.objects.get)(id=product_id)
    
        @sync_to_async
        def update_stock():
            with transaction.atomic():
                warehouse, _ = Warehouse.objects.get_or_create(product=product)
                if warehouse.quantity >= quantity:
                    warehouse.quantity -= quantity
                    warehouse.save()
                    
                    Transaction.objects.create(
                        product=product, transaction_type='out', quantity=quantity
                    )
                    
                    if warehouse.quantity <= 5:
                        return "critical"
                    elif warehouse.quantity <= 10:
                        return "low"
                    return "ok"
                return "error"
        
        status = await update_stock()
        if status == "error":
            await update.message.reply_text(f"\u274c Omborda {product.name} yetarli emas!")
        else:
            await update.message.reply_text(f"\u2705 {product.name} mahsulotidan {quantity} {product.unit} kamaytirildi!")
            if status == "low":
                await update.message.reply_text(f"\u26a0\ufe0f Diqqat! {product.name} mahsuloti omborda 10 tadan kam qoldi!")
            elif status == "critical":
                await update.message.reply_text(f"\u2757 Ogohlantirish! {product.name} mahsuloti 5 tadan kam qoldi!")
    except ValueError:
        await update.message.reply_text("\u274c Xatolik! Iltimos, faqat son kiriting.")
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text("\ud83d\udeab Bekor qilindi.")
    return ConversationHandler.END

minus_product_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(minus_product, pattern=r"^MINUS_PRODUCT$")],
    states={
        "MCATEGORY_SELECT": [CallbackQueryHandler(category_selected, pattern=r"^category_\d+$")],
        "MPRODUCT_SELECT": [CallbackQueryHandler(product_selected, pattern=r"^minusproduct_\d+$")],
        "MQUANTITY_SELECT": [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_decrease)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

