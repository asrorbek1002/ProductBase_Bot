from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from django.db.models import Count
from django.db.models import Sum, F
from asgiref.sync import sync_to_async
from bot.models import Warehouse, Category
from telegram import Update
from telegram.ext import ContextTypes

@sync_to_async
def calculate_warehouse_summary():
    result = Warehouse.objects.aggregate(
        total_value=Sum(F('quantity') * F('product__selling_price')),
        total_profit=Sum(F('quantity') * (F('product__selling_price') - F('product__purchase_price')))
    )

    return {
        'total_value': result['total_value'] or 0,
        'total_profit': result['total_profit'] or 0
    }



@sync_to_async
def get_category_buttons():
    """Kategoriya nomi va mahsulot soni bilan inline buttonlarni qaytaradi"""
    categories = Category.objects.annotate(product_count=Count('product'))

    keyboard = []
    row = []

    for index, category in enumerate(categories, start=1):
        button_text = f"{category.name} ({category.product_count})"
        button = InlineKeyboardButton(text=button_text, callback_data=f"pricecategory_{category.id}")
        row.append(button)

        # Har 3 ta tugmadan keyin yangi qator ochamiz
        if index % 3 == 0:
            keyboard.append(row)
            row = []

    # Oxirgi qatorni qo‘shamiz (agar tugmalar soni 3 ga bo‘linmasa)
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🏠 Asosiy menyu", callback_data="Main_Menu")])
    return InlineKeyboardMarkup(keyboard)


async def total_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    bot = await context.bot.get_me()
    summary  = await calculate_warehouse_summary()
    msg = f"@{bot.username} bot omborida mavjud mahsulotlar narxi:\n\n\tUmumiy narxi: {summary['total_value']}\n\tSof foyda: {summary['total_profit']}" 
    text = (
        "📦 <b>Ombordagi mavjud mahsulotlar:</b> \n\n"
        f"💰 <b>Umumiy narxi:</b> <b>{summary['total_value']:,} so'm</b> \n"
        f"💵 <b>Sof foyda:</b> <b>{summary['total_profit']:,} so'm</b> \n\n"
        "📊 <b>Ombordagi kategoriyalar bo'yicha narxlar uchun pastdagi tugmalarni tanlang!</b>"
    )
    reply_markup = await get_category_buttons()
    await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=reply_markup)


@sync_to_async
def calculate_warehouse_summary_category(category_id):
    """Berilgan kategoriyaga tegishli mahsulotlarning umumiy narxi va sof foydasini hisoblaydi"""
    result = Warehouse.objects.filter(product__category_id=category_id).aggregate(
        total_value=Sum(F('quantity') * F('product__selling_price')),
        total_profit=Sum(F('quantity') * (F('product__selling_price') - F('product__purchase_price')))
    )

    return {
        'total_value': result['total_value'] or 0,
        'total_profit': result['total_profit'] or 0
    }

# Define a variable to store the previous message's content and markup
last_message_content = None
last_reply_markup = None

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kategoriya tugmasi bosilganda mahsulotlarning umumiy narxi va foydasini chiqaradi"""
    global last_message_content, last_reply_markup
    
    query = update.callback_query
    category_id = int(query.data.split('_')[1])

    # Get the category object from the database
    category = await sync_to_async(Category.objects.get)(id=category_id)
    
    # Calculate the summary for the given category
    summary = await calculate_warehouse_summary_category(category_id)

    message = (
        f"📦 <b>Ombordagi mahsulotlar {category.name} bo‘yicha</b>\n\n"
        f"💰 <b>Umumiy narxi:</b> <b>{summary['total_value']:,} so'm</b>\n"
        f"💵 <b>Sof foyda:</b> <b>{summary['total_profit']:,} so'm</b>"
    )
    
    # Get the category buttons
    reply_markup = await get_category_buttons()

    # Check if the new message and reply_markup are different from the last ones
    if message != last_message_content or reply_markup != last_reply_markup:
        # Send the message in HTML format if there's a change
        await query.edit_message_text(message, parse_mode="HTML", reply_markup=reply_markup)
        
        # Update the last message content and reply markup
        last_message_content = message
        last_reply_markup = reply_markup

    await query.answer()
