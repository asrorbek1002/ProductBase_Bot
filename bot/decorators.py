from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .models import TelegramUser

lists = ["administrator", "member", "creator"]

def admin_required(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        # Adminni tekshirish
        try:
            user = await TelegramUser.objects.aget(user_id=user_id)
            if not user.is_admin:
                await context.bot.send_message(chat_id=user_id, text="Siz admin emassiz!😠")
                return ConversationHandler.END
                
        except TelegramUser.DoesNotExist:
            await context.bot.send_message(chat_id=user_id, text="Sizning ma'lumotlaringiz topilmadi.\n/start")
            return ConversationHandler.END
        
        # Agar admin bo‘lsa, funksiya chaqiriladi
        return await func(update, context, *args, **kwargs)
    return wrapper



