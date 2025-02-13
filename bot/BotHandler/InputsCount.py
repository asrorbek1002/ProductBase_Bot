from django.utils.timezone import now, timedelta
from django.db.models import Sum, F, Count
from asgiref.sync import sync_to_async
from bot.models import Transaction
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

# Inline tugmalar yaratish funksiyasi
def get_time_range_buttons():
    buttons = [
        [
            InlineKeyboardButton("7 kun", callback_data="countstats_7"),
            InlineKeyboardButton("10 kun", callback_data="countstats_10"),
            InlineKeyboardButton("15 kun", callback_data="countstats_15")
        ],
        [
            InlineKeyboardButton("1 oy", callback_data="countstats_30"),
            InlineKeyboardButton("3 oy", callback_data="countstats_90"),
            InlineKeyboardButton("6 oy", callback_data="countstats_180")
        ],
        [
            InlineKeyboardButton("1 yil", callback_data="countstats_365"),
            InlineKeyboardButton("Boshidan beri", callback_data="countstats_all")
        ],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="Main_Menu")]
    ]
    return InlineKeyboardMarkup(buttons)

@sync_to_async
def calculate_transaction_count(transaction_type, days=None):
    filter_params = {'transaction_type': transaction_type}

    if days is not None:
        if days == 1:  # Agar faqat bugungi ma'lumotlar kerak bo‘lsa
            filter_params['transaction_date__date'] = now().date()
        else:
            start_date = now().date() - timedelta(days=days)
            filter_params['transaction_date__date__gte'] = start_date

    transactions = (
        Transaction.objects
        .filter(**filter_params)
        .values('product')  # Har bir mahsulot uchun guruhlash
        .annotate(total_quantity=Sum('quantity'))  # Har bir mahsulot bo‘yicha umumiy miqdorni hisoblash
    )

    total_transactions = transactions.count()  # Nechta turdagi mahsulot qo‘shilganligini olish
    total_quantity = sum(item['total_quantity'] for item in transactions)  # Umumiy miqdorni hisoblash

    return {
        'total_transactions': total_transactions,
        'total_quantity': total_quantity
    }


# Omborga qo‘shilgan mahsulotlarni chiqarish
async def added_products_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer('📦 Omborga qo‘shilgan mahsulotlar yuklanmoqda...')
    
    products_count = await calculate_transaction_count('in', days=1)
    if not products_count:
        caption = "📦 Bugun omborga hech qanday mahsulot qo‘shilmadi."
    else:
        caption = f"📦 <b>Bugun omborga {products_count['total_transactions']} xil mahsulotdan {products_count['total_quantity']} ta qo'shildi</b>"
    
    await query.edit_message_text(text=caption, parse_mode='HTML', reply_markup=get_time_range_buttons())



# Vaqt oralig'iga mos statistikani chiqarish
async def time_range_stats_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer('📊 Hisoblanmoqda...')
    
    period = query.data.split('_')[1]
    days = int(period) if period != 'all' else None
    
    expense = await calculate_transaction_count('in', days=days)
    
    caption = (
        f"📊 <b>Oxirgi {period if days else 'barcha'} kunda qo'shilgan mahsulotlar soni</b>\n\n"
        f"{expense['total_transactions']} xil mahsulotdan {expense['total_quantity']} ta qo'shilgan"
    )
    
    await query.edit_message_text(text=caption, parse_mode='HTML', reply_markup=get_time_range_buttons())
