from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from bot.models import Category
from asgiref.sync import sync_to_async



async def start_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start category creation."""
    await update.callback_query.edit_message_text("Yangi kategoriya nomini kiriting:")
    return "CATEGORY_NAME"


async def category_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save category name and add to database."""
    category_name = update.message.text
    category = await sync_to_async(Category.objects.create)(name=category_name)
    await update.message.reply_text(f"Kategoriya qo'shildi: {category.name}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the conversation."""
    await update.message.reply_text("Bekor qilindi.")
    return ConversationHandler.END


add_category_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add_category, pattern=r"^ADD_CATEGORY$")],
    states={
        "CATEGORY_NAME": [MessageHandler(filters.TEXT & ~filters.COMMAND, category_name)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)