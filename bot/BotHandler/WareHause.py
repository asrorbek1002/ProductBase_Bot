from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackQueryHandler
from asgiref.sync import sync_to_async
from bot.models import Product, Warehouse, Transaction, Category
from django.db.models import Sum, F
from django.utils.timezone import now
from datetime import timedelta

def back_main_menu_buttons():
    return [[InlineKeyboardButton("🔙 Orqaga", callback_data="main_menu")]]

async def CategoryList(update: Update, context):
    categories = await sync_to_async(list)(Category.objects.all())
    keyboard = []
    row = []
    
    for i, cat in enumerate(categories, start=1):
        row.append(InlineKeyboardButton(f"{cat.name} ({await sync_to_async(Product.objects.filter(category=cat).count)()})", callback_data=f"Listcategory_{cat.id}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # for cat in categories:
    #     count = await sync_to_async(Product.objects.filter(category=cat).count)()
    #     keyboard.append([InlineKeyboardButton(f"{cat.name} ({count})", callback_data=f"Listcategory_{cat.id}")])
    
    keyboard += back_main_menu_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text("Kategoriyani tanlang:", reply_markup=reply_markup)

async def ProductList(update: Update, context):
    query = update.callback_query
    await query.answer()
    category_id = int(query.data.split('_')[1])

    products = await sync_to_async(list)(Product.objects.filter(category_id=category_id))
    keyboard = []
    
    keyboard = []
    row = []
    for i, product in enumerate(products, start=1):
        quantity = await sync_to_async(lambda: Warehouse.objects.filter(product=product).aggregate(total=Sum("quantity"))["total"] or 0)()

        row.append(InlineKeyboardButton(f"{product.name} ({quantity})", callback_data=f"editproduct_{product.id}"))
        if i % 4 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    # reply_markup = InlineKeyboardMarkup(keyboard)

    # for prod in products:
    #     keyboard.append([InlineKeyboardButton(f"{prod.name} ({quantity})", callback_data=f"editproduct_{prod.id}")])

    keyboard += back_main_menu_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Mahsulotni tanlang:", reply_markup=reply_markup)

from django.db.models import F



@sync_to_async
def calculate_product_stats(product_id, days=None):
    filter_params = {'product_id': product_id}
    
    if days is not None:
        start_date = now().date() - timedelta(days=days)
        filter_params['transaction_date__date__gte'] = start_date

    added = (
        Transaction.objects
        .filter(**filter_params, transaction_type="in")
        .aggregate(total=Sum('quantity'))['total'] or 0
    )

    sold = (
        Transaction.objects
        .filter(**filter_params, transaction_type="out")
        .aggregate(total=Sum('quantity'))['total'] or 0
    )

    total_in_warehouse = Warehouse.objects.filter(product_id=product_id).aggregate(total=Sum("quantity"))['total'] or 0

    # Mahsulotning jami narxini hisoblash
    product = Product.objects.get(id=product_id)
    total_price = total_in_warehouse * product.selling_price  # Ombordagi jami narx (selling_price * quantity)
    purchase_prise = total_in_warehouse * product.purchase_price
    # Sotilgan va sotib olingan narxlarni miqdor bilan ko'paytirish
    sold_price = (
        Transaction.objects
        .filter(**filter_params, transaction_type="out")
        .aggregate(total=Sum(F("quantity") * F("product__selling_price")))['total'] or 0
    )

    bought_price = (
        Transaction.objects
        .filter(**filter_params, transaction_type="in")
        .aggregate(total=Sum(F("quantity") * F("product__purchase_price")))['total'] or 0
    )
    
    # Sof foyda hisoblashda sotilgan narxdan sotib olingan narxni ayiramiz
    net_profit = total_price - purchase_prise  # Sof foyda

    # Mahsulot nomi va sotish narxini qaytarish
    return {
        "product_name": product.name,
        "selling_price": product.selling_price,
        "added": added,
        "sold": sold,
        "total_in_warehouse": total_in_warehouse,
        "total_price": total_price,
        "net_profit": net_profit
    }




async def product_stats(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[1])
    stats = await calculate_product_stats(product_id, days=3)

    text = (
        f"📊 <b>Mahsulot statistikasi (oxirgi 3 kun)</b>\n\n"
        f"🛍 Mahsulot: <b>{stats['product_name']}</b>\n"
        f"💸 Sotish narxi: <b>{stats['selling_price']:,} so‘m</b>\n\n"
        f"📥 Omborga qo‘shildi: <b>{stats['added']} ta</b>\n"
        f"📤 Sotildi: <b>{stats['sold']} ta {(stats['sold'] * stats['selling_price']):,} so'm</b>\n"
        f"📦 Omborda: <b>{stats['total_in_warehouse']} ta</b>\n"
        f"💰 Umumiy narxi: <b>{stats['total_price']:,} so‘m</b>\n"
        f"💵 Sof foyda (<i>ko'riladigan</i>): <b>{stats['net_profit']:,} so‘m</b>\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("10 kun", callback_data=f"aprodstat_10_{product_id}"),
            InlineKeyboardButton("1 oy", callback_data=f"aprodstat_30_{product_id}")
        ],
        [
            InlineKeyboardButton("6 oy", callback_data=f"aprodstat_180_{product_id}"),
            InlineKeyboardButton("1 yil", callback_data=f"aprodstat_365_{product_id}")
        ],
        [InlineKeyboardButton("Boshidan beri", callback_data=f"aprodstat_all_{product_id}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="lists_product")]
    ]
    
    await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))


async def time_range_product_stats(update: Update, context):
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split('_')
    period = data_parts[1]
    product_id = int(data_parts[2])

    days = int(period) if period != "all" else None
    stats = await calculate_product_stats(product_id, days=days)

    caption = (
        f"📊 <b>Oxirgi {period if days else 'barcha'} kunda mahsulot statistikasi</b>\n\n"
        f"🛍 Mahsulot: <b>{stats['product_name']}</b>\n"
        f"💸 Sotish narxi: <b>{stats['selling_price']:,} so‘m</b>\n\n"
        f"📥 Omborga qo‘shildi: <b>{stats['added']} ta</b>\n"
        f"📤 Sotildi: <b>{stats['sold']} ta {(stats['sold'] * stats['selling_price']):,} so'm</b>\n"
        f"📦 Omborda: <b>{stats['total_in_warehouse']} ta</b>\n"
        f"💰 Umumiy narxi: <b>{stats['total_price']:,} so‘m</b>\n"
        f"💵 Sof foyda (<i>ko'riladigan</i>): <b>{stats['net_profit']:,} so‘m</b>\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("10 kun", callback_data=f"aprodstat_10_{product_id}"),
            InlineKeyboardButton("1 oy", callback_data=f"aprodstat_30_{product_id}")
        ],
        [
            InlineKeyboardButton("6 oy", callback_data=f"aprodstat_180_{product_id}"),
            InlineKeyboardButton("1 yil", callback_data=f"aprodstat_365_{product_id}")
        ],
        [InlineKeyboardButton("Boshidan beri", callback_data=f"aprodstat_all_{product_id}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="Product_List")]
    ]

    await query.edit_message_text(text=caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
