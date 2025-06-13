import asyncio
from django.core.management.base import BaseCommand
from bot_analytics.bot import bot_instance

class Command(BaseCommand):
	help = 'Run the Telegram bot'
	
	def handle(self, *args, **options):
		self.stdout.write(self.style.SUCCESS('Starting Telegram bot ...'))

		try:
			bot_instance.application.run_polling(
				allowed_updates = ['message', 'callback_query', 'inline_query']
			)
		except KeyboardInterrupt:
			self.stdout.write(self.style.WARNING('Bot stopped by user'))
		except Exception as e:
			self.stdout.write(self.style.ERROR(f'Bot error {str(e)}'))





