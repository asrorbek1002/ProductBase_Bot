from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, F
from config.settings import TELEGRAM_BOT_TOKEN as TOKEN
from asgiref.sync import sync_to_async


# Django sozlamalari
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from bot.models import Transaction  # Transaction modelini import qiling

# Bot tokeni
from datetime import timedelta
import datetime
from django.utils import timezone
from telegram import Update
from telegram.ext import ContextTypes

# Kunlik hisobot
async def daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = timezone.localtime().date()  # Vaqt zonali holatda olish
    start_date = timezone.make_aware(datetime.datetime.combine(today, datetime.time.min))
    end_date = timezone.make_aware(datetime.datetime.combine(today + timedelta(days=1), datetime.time.min))
    
    profit_loss = await calculate_profit_loss(start_date, end_date)
    await update.message.reply_text(f"📊 Kunlik hisobot:\nSof foyda: {profit_loss} so'm")

# Haftalik hisobot
async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = timezone.localtime().date()
    start_date = today - timedelta(days=today.weekday())
    start_date = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_date = start_date + timedelta(days=7)
    
    profit_loss = await calculate_profit_loss(start_date, end_date)
    await update.message.reply_text(f"📊 Haftalik hisobot:\nSof foyda: {profit_loss} so'm")

# Oylik hisobot
async def monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = timezone.localtime().date()
    start_date = today.replace(day=1)
    start_date = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_date = start_date + timedelta(days=31)  # Bu aniq emas, oyni oxirgi kunini olish kerak

    profit_loss = await calculate_profit_loss(start_date, end_date)
    await update.message.reply_text(f"📊 Oylik hisobot:\nSof foyda: {profit_loss} so'm")

# Yillik hisobot
async def yearly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = timezone.localtime().date()
    start_date = today.replace(month=1, day=1)
    start_date = timezone.make_aware(datetime.datetime.combine(start_date, datetime.time.min))
    end_date = start_date.replace(year=start_date.year + 1)

    profit_loss = await calculate_profit_loss(start_date, end_date)
    await update.message.reply_text(f"📊 Yillik hisobot:\nSof foyda: {profit_loss} so'm")

from django.db.models import Sum, F
from asgiref.sync import sync_to_async
from django.utils import timezone

async def calculate_profit_loss(start_date, end_date):
    print("Hisoblanayotgan vaqt oralig'i:")
    print("Boshlanish:", start_date)
    print("Tugash:", end_date)

    # Vaqt zonalarini to‘g‘rilash (agar kerak bo‘lsa)
    if timezone.is_naive(start_date):
        start_date = timezone.make_aware(start_date)
    if timezone.is_naive(end_date):
        end_date = timezone.make_aware(end_date)

    # Barcha tranzaktsiyalarni olish
    @sync_to_async
    def get_transactions():
        return list(Transaction.objects.filter(transaction_date__range=(start_date, end_date)))

    transactions = await get_transactions()

    if not transactions:
        print("❗ Transaction topilmadi.")
        return 0  # Agar ma’lumot bo‘lmasa, 0 qaytarish

    # Foydani hisoblash
    @sync_to_async
    def calculate_total_profit():
        return Transaction.objects.filter(transaction_date__range=(start_date, end_date), transaction_type='out')\
            .annotate(
                profit_per_item=F('product__selling_price') - F('product__purchase_price'),
                total_profit=F('profit_per_item') * F('quantity')
            ).aggregate(total_profit=Sum('total_profit'))['total_profit'] or 0  # None bo‘lsa 0 qaytarish

    total_profit = await calculate_total_profit()

    print("✅ Sof foyda:", total_profit)
    return total_profit



# Botni ishga tushurish
def main():
    application = Application.builder().token(TOKEN).build()

    # CommandHandler qo'shish
    application.add_handler(CommandHandler("daily", daily_report))
    application.add_handler(CommandHandler("weekly", weekly_report))
    application.add_handler(CommandHandler("monthly", monthly_report))
    application.add_handler(CommandHandler("yearly", yearly_report))

    # Botni ishga tushurish
    application.run_polling()

if __name__ == "__main__":
    main()