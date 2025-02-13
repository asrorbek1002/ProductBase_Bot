from django.utils.timezone import now, timedelta
from django.db.models import Sum, F
from asgiref.sync import sync_to_async
from bot.models import Transaction
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

@sync_to_async
def calculate_transaction_summary(transaction_type, days=None):
    filter_params = {'transaction_type': transaction_type}
    
    # 1 kunlik statistikani olish uchun, kecha boshlanish sanasini hisoblash
    if days is not None:
        # Bugundan 1 kun oldingi sanani olish
        start_date = (now().date() + timedelta(days=1)) - timedelta(days=days)
        filter_params['transaction_date__date__gte'] = start_date

    # Filtrlangan ma'lumotlarni olish
    total = (
        Transaction.objects
        .filter(**filter_params)
        .aggregate(total_amount=Sum(F('quantity') * F('product__purchase_price')))
    )
    
    return total['total_amount'] or 0

# Inline tugmalar yaratish funksiyasi
def get_time_range_buttons():
    buttons = [
        [
            InlineKeyboardButton("1 hafta", callback_data="stats_7"),
            InlineKeyboardButton("10 kun", callback_data="stats_10"),
            InlineKeyboardButton("15 kun", callback_data="stats_15")
        ],
        [
            InlineKeyboardButton("1 oy", callback_data="stats_30"),
            InlineKeyboardButton("3 oy", callback_data="stats_90"),
            InlineKeyboardButton("6 oy", callback_data="stats_180")
        ],
        [
            InlineKeyboardButton("1 yil", callback_data="stats_365"),
            InlineKeyboardButton("Boshidan beri", callback_data="stats_all")
        ],
        [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="Main_Menu")]
    ]
    return InlineKeyboardMarkup(buttons)

# Statistika chiqarish funksiyasi
async def transaction_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer('📊 Statistika yuklanmoqda...')
    
    income = await calculate_transaction_summary('out', days=1)
    expense = await calculate_transaction_summary('in', days=1)
    
    caption = (
        f"📊 <b>Bugungi tranzaksiyalar</b>\n\n"
        f"💰 <b>Sotuv:</b> {income:,} so'm\n"
        f"📉 <b>Xarid:</b> {expense:,} so'm"
    )
    
    await query.edit_message_text(text=caption, parse_mode='HTML', reply_markup=get_time_range_buttons())

# Vaqt oralig'iga mos statistikani chiqarish
async def time_range_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer('📊 Hisoblanmoqda...')
    
    period = query.data.split('_')[1]
    days = int(period) if period != 'all' else None
    
    income = await calculate_transaction_summary('out', days=days)
    expense = await calculate_transaction_summary('in', days=days)
    
    caption = (
        f"📊 <b>Oxirgi {period if days else 'barcha'} kunlik tranzaksiyalar</b>\n\n"
        f"💰 <b>Sotuv:</b> {income:,} so'm\n"
        f"📉 <b>Xarid:</b> {expense:,} so'm"
    )
    
    await query.edit_message_text(text=caption, parse_mode='HTML', reply_markup=get_time_range_buttons())
