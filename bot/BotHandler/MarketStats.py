from django.utils.timezone import now
from django.db.models import Sum, F
from asgiref.sync import sync_to_async
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from bot.models import Transaction
from telegram.ext import ContextTypes

# 🔝 Eng ko‘p sotilgan mahsulotlar
@sync_to_async
def get_top_10_sold_products():
    today = now().date()
    return list(
        Transaction.objects
        .filter(transaction_type='out', transaction_date__date=today)
        .values('product__name', 'product__unit')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:10]
    )

# 💰 Foydani hisoblash
@sync_to_async
def calculate_income():
    result = Transaction.objects.filter(transaction_type='out').aggregate(
        total_income=Sum(F('quantity') * (F('product__selling_price') - F('product__purchase_price')))
    )
    return result['total_income'] or 0

# 📉 Xarajatni hisoblash
@sync_to_async
def calculate_expense():
    result = Transaction.objects.filter(transaction_type='in').aggregate(
        total_expense=Sum(F('quantity') * F('product__purchase_price'))
    )
    return result['total_expense'] or 0

# 📊 Statistika tugmalari
stats_markup = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("📥 Kirim/Chiqim", callback_data="input_output_M"),
        InlineKeyboardButton("💵 Jami narx", callback_data="All_price")
    ],
    [
        InlineKeyboardButton("📦 Omborga qo‘shilganlar", callback_data="Added_to_base"),
        # InlineKeyboardButton("🛒 Sotilganlar", callback_data="Sold_out")
    ]
])

# 📊 Statistika chiqarish funksiyasi
async def Market_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("📊 Statistika yuklanmoqda...")
    await query.delete_message()
    
    bot = await context.bot.get_me()
    bot_id = bot.id  

    # 🔄 Ma'lumotlarni olish
    photos = await context.bot.get_user_profile_photos(bot_id)
    products, income, expense = await get_top_10_sold_products(), await calculate_income(), await calculate_expense()

    # 🏷 Mahsulotlar ro‘yxatini tayyorlash
    product_text = "\n".join([
        f"🏷 {item['product__name']} ({item['product__unit']}): {item['total_sold']} {item['product__unit']}" 
        for item in products
    ]) or "🚫 Ma'lumot topilmadi"

    # 📋 Yakuniy xabar
    caption = (
        f"✨ <b>{bot.first_name} Statistikasi</b> ✨\n\n"
        f"🔝 <b>Bugungi eng ko‘p sotilgan mahsulotlar:</b>\n{product_text}\n\n"
        f"💰 <b>Foyda:</b> {income:,} so‘m\n"
        f"📉 <b>Xarajat:</b> {expense:,} so‘m"
    )

    # 🖼 Profil rasmi bilan xabar jo‘natish
    if photos.total_count > 0:
        file_id = photos.photos[0][0].file_id
        await context.bot.send_photo(
            chat_id=update.effective_user.id, 
            photo=file_id, 
            caption=caption, 
            parse_mode='HTML', 
            reply_markup=stats_markup
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_user.id, 
            text=caption, 
            parse_mode='HTML', 
            reply_markup=stats_markup
        )
