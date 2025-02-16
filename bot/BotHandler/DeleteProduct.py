from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler, ConversationHandler
from asgiref.sync import sync_to_async
from django.db.models import Count
from bot.models import Category, Product
from django.core.exceptions import ObjectDoesNotExist

# States

from asgiref.sync import sync_to_async
from django.db.models import Count

# Asinxron kontekstda ishlash uchun count() ni sync_to_async bilan chaqirishingiz kerak
async def delete_product_start(update: Update, context: CallbackContext):
    """Start deleting a product by showing categories."""
    categories = await sync_to_async(list)(Category.objects.all())

    if not categories:
        await update.callback_query.answer("Kategoriyalar mavjud emas!")
        return ConversationHandler.END

    keyboard = []

    for cat in categories:
        # Asinxron tarzda count() ni chaqirish uchun uni sync_to_async yordamida o'rab oldik
        count = await sync_to_async(lambda: Product.objects.filter(category=cat).aggregate(Count('id')))()
        count_value = count['id__count'] if count else 0

        keyboard.append([InlineKeyboardButton(f"{cat.name} ({count_value})", callback_data=f"delete_cat_{cat.id}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Mahsulot turini tanlang:", reply_markup=reply_markup)
    return "SELECT_CATEGORY"


async def select_category(update: Update, context: CallbackContext):
    """Show products in the selected category."""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[2])
    category = await sync_to_async(Category.objects.get)(id=category_id)
    products = await sync_to_async(list)(Product.objects.filter(category=category))
    
    if not products:
        await query.message.reply_text("Bu kategoriyada mahsulot yo'q!")
        return ConversationHandler.END
    
    keyboard = []
    row = []
    for i, product in enumerate(products, start=1):
        row.append(InlineKeyboardButton(product.name, callback_data=f"delete_prod_{product.id}"))
        if i % 4 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(f"{category.name} dagi mahsulotlar:", reply_markup=reply_markup)
    return "SELECT_PRODUCT"

async def confirm_delete(update: Update, context: CallbackContext):
    """Ask for confirmation before deleting the product."""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split("_")[2])
    context.user_data['delete_product_id'] = product_id
    product = await sync_to_async(Product.objects.get)(id=product_id)
    
    keyboard = [
        [InlineKeyboardButton("✅ Ha", callback_data="confirm_delete")],
        [InlineKeyboardButton("❌ Yo'q", callback_data="cancel_delete")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(f"{product.name} mahsulotini o‘chirishni tasdiqlaysizmi?", reply_markup=reply_markup)
    return "CONFIRM_DELETE"

async def delete_product(update: Update, context: CallbackContext):
    """Delete the selected product."""
    query = update.callback_query
    await query.answer()
    
    product_id = context.user_data.get('delete_product_id')
    try:
        product = await sync_to_async(Product.objects.get)(id=product_id)
        await sync_to_async(product.delete)()
        await query.message.reply_text("✅ Mahsulot muvaffaqiyatli o‘chirildi!")
    except ObjectDoesNotExist:
        await query.message.reply_text("❌ Mahsulot topilmadi!")
    
    return ConversationHandler.END

async def cancel_delete(update: Update, context: CallbackContext):
    """Cancel the deletion process."""
    await update.callback_query.message.reply_text("🚫 Mahsulot o‘chirish bekor qilindi.")
    return ConversationHandler.END

# ConversationHandler
delete_product_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(delete_product_start, pattern=r"^delete_product_to_base$")],
    states={
        "SELECT_CATEGORY": [CallbackQueryHandler(select_category, pattern=r"^delete_cat_\d+$")],
        "SELECT_PRODUCT": [CallbackQueryHandler(confirm_delete, pattern=r"^delete_prod_\d+$")],
        "CONFIRM_DELETE": [
            CallbackQueryHandler(delete_product, pattern=r"^confirm_delete$")],
    },
    fallbacks=[CallbackQueryHandler(cancel_delete, pattern=r"^cancel_delete$")],
)
