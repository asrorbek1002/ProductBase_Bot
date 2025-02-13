from django.contrib import admin
from .models import TelegramUser, UserMessage, Product, Category, Transaction, Warehouse

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity')
    list_filter = ('product',)

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'first_name', 'username', 'is_admin', 'date_joined', 'last_active')
    list_filter = ('is_admin',)
    search_fields = ('user_id', 'first_name', 'username')
    ordering = ('-date_joined',)
    list_per_page = 20


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'purchase_price', 'selling_price', 'get_stock', 'unit', 'profit')
    list_filter = ('category',)
    search_fields = ('name',)
    readonly_fields = ('profit',)

    def get_stock(self, obj):
        return obj.warehouse.quantity if obj.warehouse else "N/A"

    get_stock.short_description = "Stock Quantity"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'get_stock', 'transaction_date')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('product__name',)
    date_hierarchy = 'transaction_date'

    def get_stock(self, obj):
        return obj.product.warehouse.quantity if obj.product and obj.product.warehouse else "N/A"

    get_stock.short_description = "Stock Quantity"


@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'message', 'sent_at')
    search_fields = ('user_name', 'message')
    list_per_page = 50
