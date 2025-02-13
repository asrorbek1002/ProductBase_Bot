from django.core.management.base import BaseCommand
from bot.main import main


class Command(BaseCommand):
    help = 'Starts the Telegram bot'

    def handle(self, *args, **kwargs):
        main()