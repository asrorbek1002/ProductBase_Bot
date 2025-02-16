from django.db import models
from asgiref.sync import sync_to_async
from django.db.models import Count
from django.utils.timezone import now

# Telegram foydalanuvchilari modeli
class TelegramUser(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    user_id = models.BigIntegerField(unique=True, verbose_name="Telegram User ID")
    first_name = models.CharField(max_length=256, blank=True, null=True, verbose_name="First Name")
    username = models.CharField(max_length=256, blank=True, null=True, verbose_name="Username")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date Joined")
    last_active = models.DateTimeField(auto_now=True, verbose_name="Last Active")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="User Status")
    is_admin = models.BooleanField(default=False, verbose_name="Is Admin")
    reff = models.PositiveIntegerField(default=0, verbose_name="User Referral Count")

    class Meta:
        verbose_name = "Telegram User"
        verbose_name_plural = "Telegram Users"
        ordering = ['-last_active']

    def __str__(self):
        return f"{self.first_name} (@{self.username})" if self.username else f"{self.user_id}"


    @classmethod
    async def get_admin_ids(cls):
        """
        Admin bo'lgan userlarning IDlarini qaytaradi.
        """
        return await sync_to_async(
            lambda: list(cls.objects.filter(is_admin=True).values_list('user_id', flat=True))
        )()


    @classmethod
    async def get_today_new_users(cls):
        """
        Bugungi yangi foydalanuvchilarni qaytaradi.
        """
        today = now().date()
        return await sync_to_async(lambda: list(cls.objects.filter(date_joined__date=today)))()

    @classmethod
    async def get_daily_new_users(cls):
        """
        Har bir kun uchun yangi foydalanuvchilar sonini qaytaradi.
        """
        return await sync_to_async(
            lambda: list(cls.objects.values('date_joined__date').annotate(count=Count('id')).order_by('-date_joined__date'))
        )()

    @classmethod
    async def get_total_users(cls):
        """
        Umumiy foydalanuvchilar sonini qaytaradi.
        """
        return await sync_to_async(cls.objects.count)()

    @classmethod
    async def count_admin_users(cls):
        """
        Admin bo'lgan foydalanuvchilar sonini qaytaradi.
        """
        return await sync_to_async(lambda: cls.objects.filter(is_admin=True).count())()

    @classmethod
    async def find_inactive_users(cls, bot_token):
        """
        Nofaol foydalanuvchilarni aniqlaydi.
        :param bot_token: Telegram bot tokeni
        :return: Bloklangan foydalanuvchilar soni
        """
        from telegram import Bot
        from telegram.error import TelegramError

        bot = Bot(token=bot_token)
        blocked_users_count = 0

        # SyncToAsync faqat Django ORM bilan ishlashda kerak
        users = await sync_to_async(lambda: list(cls.objects.all()))()

        for user in users:
            try:
                await bot.send_chat_action(chat_id=user.user_id, action="typing")
            except TelegramError:
                blocked_users_count += 1

        return blocked_users_count

    @classmethod
    async def make_admin(cls, user_id):
        """
        Userni admin qiladi.
        :param user_id: Admin qilinadigan foydalanuvchining Telegram user_id-si
        :return: Yangilangan user obyekti yoki None (user topilmasa)
        """
        try:
            user = await sync_to_async(cls.objects.get)(user_id=user_id)
            user.is_admin = True
            await sync_to_async(user.save)(update_fields=['is_admin'])
            return user
        except cls.DoesNotExist:
            print(f"User with ID {user_id} does not exist.")
            return None

    @classmethod
    async def remove_admin(cls, user_id):
        """
        Userni adminlikdan chiqaradi.
        :param user_id: Adminlikdan chiqariladigan foydalanuvchining Telegram user_id-si
        :return: Yangilangan user obyekti yoki None (user topilmasa)
        """
        try:
            user = await sync_to_async(cls.objects.get)(user_id=user_id)
            user.is_admin = False
            await sync_to_async(user.save)(update_fields=['is_admin'])
            return user
        except cls.DoesNotExist:
            print(f"User with ID {user_id} does not exist.")
            return None





# Kategoriya modeli
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Turkum nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Izoh")

    class Meta:
        verbose_name = "Turkum"
        verbose_name_plural = "Turkumlar"

    def __str__(self):
        return self.name


# Mahsulot modeli (quantity olib tashlandi, endi Warehouse modelida saqlanadi)
class Product(models.Model):
    UNIT_CHOICES = [
        ('dona', 'Dona'),
        ('litr', 'Litr'),
        ('kg', 'Kilogram'),
        ('m', 'Metr'),
        ('block', 'Block'),
    ]

    name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    category = models.ForeignKey(Category, on_delete=models.DO_NOTHING, null=True, verbose_name="Turkum")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Sotib olish narxi")
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Sotish narxi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Mahsulot qo'shilgan vaqt")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs', verbose_name="Tovar birligi")

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def profit(self):
        return self.selling_price - self.purchase_price

    def __str__(self):
        return f"{self.name} ({self.category.name})"


# Ombor (Warehouse) modeli - mahsulotning miqdori shu yerdan boshqariladi
class Warehouse(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Miqdori")

    class Meta:
        verbose_name = "Ombor"
        verbose_name_plural = "Omborlar"

    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.product.get_unit_display()}"


# Tranzaksiya modeli
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('in', 'Kirim'),
        ('out', 'Chiqim'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Mahsulot")
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES, verbose_name="Tranzaksiya turi")
    quantity = models.PositiveIntegerField(verbose_name="Miqdori")
    transaction_date = models.DateTimeField(auto_now_add=True, verbose_name="Tranzaksiya sanasi")

    class Meta:
        verbose_name = "Tranzaksiya"
        verbose_name_plural = "Tranzaksiyalar"

    def __str__(self):
        return f"{self.product.name} - {self.get_transaction_type_display()} ({self.quantity})"


# Foydalanuvchi xabarlari modeli
class UserMessage(models.Model):
    user_name = models.CharField(max_length=100, verbose_name="Foydalanuvchi ismi")
    message = models.TextField(verbose_name="Xabar")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")

    class Meta:
        verbose_name = "Foydalanuvchi xabari"
        verbose_name_plural = "Foydalanuvchi xabarlari"

    def __str__(self):
        return f"{self.user_name} - {self.message[:50]}..."
