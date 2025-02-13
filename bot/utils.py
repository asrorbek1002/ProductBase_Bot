from django.db.models import Sum, F
from django.db import transaction
from asgiref.sync import sync_to_async
from .models import TelegramUser, Product, Transaction
from django.utils import timezone
from datetime import timedelta

async def save_user_to_db(data):
    user_id = data.id
    first_name = data.first_name 
    username = data.username  

    try:
        # Wrap the ORM operation with sync_to_async
        @sync_to_async
        def update_or_create_user():
            return TelegramUser.objects.update_or_create(
                user_id=user_id,
                defaults={'first_name': first_name, 'username': username}
            )

        user, created = await update_or_create_user()
        return True
    except Exception as error:
        print(f"Error saving user to DB: {error}")
        return False



from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async

# calculate_profit_loss funksiya
@sync_to_async
def calculate_profit_loss(start_date, end_date):
    transactions = Transaction.objects.filter(transaction_date__range=(start_date, end_date))
    total_profit = transactions.filter(transaction_type='out').aggregate(
        total_profit=Sum(F('product__selling_price') - F('product__purchase_price') * F('quantity'))
    )['total_profit'] or 0
    return total_profit

# top_sold_products funksiya
@sync_to_async
def top_sold_products(category_id=None, limit=10):
    queryset = Transaction.objects.filter(transaction_type='out')
    if category_id:
        queryset = queryset.filter(product__category_id=category_id)
    top_products = queryset.values('product__name').annotate(
        total_sold=Sum('quantity')
    ).order_by('-total_sold')[:limit]
    return top_products

# total_inventory_value funksiya
@sync_to_async
def total_inventory_value():
    total_value = Product.objects.aggregate(
        total_value=Sum(F('quantity') * F('purchase_price'))
    )['total_value'] or 0
    return total_value

# daily_report funksiya
@sync_to_async
def daily_report():
    today = timezone.now().date()
    start_date = today
    end_date = today + timedelta(days=1)
    return calculate_profit_loss(start_date, end_date)

# weekly_report funksiya
@sync_to_async
def weekly_report():
    today = timezone.now().date()
    start_date = today - timedelta(days=today.weekday())
    end_date = start_date + timedelta(days=7)
    return calculate_profit_loss(start_date, end_date)

# monthly_report funksiya
@sync_to_async
def monthly_report():
    today = timezone.now().date()
    start_date = today.replace(day=1)
    end_date = start_date + timedelta(days=31)
    return calculate_profit_loss(start_date, end_date)

# yearly_report funksiya
@sync_to_async
def yearly_report():
    today = timezone.now().date()
    start_date = today.replace(month=1, day=1)
    end_date = start_date.replace(year=start_date.year + 1)
    return calculate_profit_loss(start_date, end_date)



async def save_transaction_async(product, transaction_type, quantity):
    @sync_to_async
    def create_transaction():
        with transaction.atomic():
            return Transaction.objects.create(
                product=product,
                transaction_type=transaction_type,
                quantity=quantity
            )
    
    return await create_transaction()
