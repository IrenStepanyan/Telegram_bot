from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from bot_analytics.models import TelegramUser, UserInteraction, BotStatistics

class Command(BaseCommand):
	help = 'Update daily statistics'

	def handle(self, *args, **options):
		today = date.today()

		stats, created = BotStatistics.objects.get_or_create(
			date = today,
			defaults = {
				'total_users': 0,
				'new_users': 0,
				'active_users': 0,
				'total_messages': 0,
				'total_commands': 0,
			}
		)

		stats.total_users = TelegramUser.objects.count()
		stats.new_users = TelegramUser.objects.filter(created_at__date=today).count()
		stats.active_users = TelegramUser.objects.filter(last_interaction__date= today).count()
		stats.total_messages = UserInteraction.objects.filter(
			timestamp__date = today,
			interaction_type = 'message'
			).count()
		stats.total_commands = UserInteraction.objects.filter(
			timestamp__date = today,
			interaction_type = 'command').count()

		stats.save()
		
		self.stdout.write(
			self.style.SUCCESS(f"Statisrics updated for {today}")
		)

