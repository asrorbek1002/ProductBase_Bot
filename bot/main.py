from telegram.ext import Application, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from telegram import Update
from config.settings import TELEGRAM_BOT_TOKEN
from .BotCommands.StartCommand import start
from .BotAdmin.AdminMenu import admin_menyu
from .BotHandler.SendMessage import send_msg_handler
from .BotHandler.BotStats import bot_stats
from .BotAdmin.AddAdmin import add_admin_handler, the_first_admin
from .BotAdmin.DeleteAdmin import remove_admin_handler
from .BotAdmin.AdminList import AdminList
from .BotHandler.TestHandler import testInlinehandler
from .BotHandler.AddProduct import add_product_handler
from .BotHandler.AddCategroy import add_category_handler
from .BotHandler.DeleteProduct import delete_product_handler
from .BotHandler.PlusProduct import plus_product_handler
from .BotHandler.MinusProduct import minus_product_handler
from .BotHandler.MarketStats import Market_stats
from .BotHandler.InputOutput import transaction_stats, time_range_stats
from .BotHandler.InputsCount import added_products_stats, time_range_stats_count
from .BotHandler.TotalPrice import total_price, category_callback
from .BotHandler.WareHause import CategoryList, ProductList, product_stats, time_range_product_stats




def main():

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands  
    app.add_handler(CommandHandler("start", start))

    app.add_handler(CommandHandler('admin_panel', admin_menyu))
    app.add_handler(CommandHandler('kjiaufuyerfgvu', the_first_admin))

    # Conversation handlers
    app.add_handler(send_msg_handler)
    app.add_handler(add_admin_handler)
    app.add_handler(remove_admin_handler)
    app.add_handler(add_product_handler)
    app.add_handler(add_category_handler)
    app.add_handler(delete_product_handler)
    app.add_handler(plus_product_handler)
    app.add_handler(minus_product_handler)

    # Inline hanlder
    app.add_handler(CallbackQueryHandler(start, pattern=r"^Main_Menu$"))
    app.add_handler(CallbackQueryHandler(bot_stats, pattern=r"^botstats$"))
    app.add_handler(CallbackQueryHandler(start, pattern=r"^Check_mandatory_channel$"))
    app.add_handler(CallbackQueryHandler(AdminList, pattern=r"^admin_list$"))
    app.add_handler(CallbackQueryHandler(start, pattern=r"^cancel$"))
    app.add_handler(CallbackQueryHandler(Market_stats, pattern=r"^Stats_Shop$"))
    app.add_handler(CallbackQueryHandler(transaction_stats, pattern=r"^input_output_M$"))
    app.add_handler(CallbackQueryHandler(time_range_stats, pattern=r"^stats_"))
    app.add_handler(CallbackQueryHandler(added_products_stats, pattern=r"^Added_to_base$"))
    app.add_handler(CallbackQueryHandler(time_range_stats_count, pattern=r"^countstats_"))
    app.add_handler(CallbackQueryHandler(total_price, pattern=r"^All_price$"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^pricecategory_"))
    app.add_handler(CallbackQueryHandler(CategoryList, pattern=r"^lists_product$"))
    app.add_handler(CallbackQueryHandler(ProductList, pattern=r"^Listcategory_"))
    app.add_handler(CallbackQueryHandler(product_stats, pattern=r"^editproduct_"))
    app.add_handler(CallbackQueryHandler(time_range_product_stats, pattern=r"^aprodstat_"))


    # Test
    app.add_handler(CallbackQueryHandler(testInlinehandler))

    # Bot start
    print("The bot is running!!!")
    app.run_polling()
