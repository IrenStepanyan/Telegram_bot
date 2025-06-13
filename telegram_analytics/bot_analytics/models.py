from django.db import models
from django.utils import timezone

class TelegramUser(models.Model):
	telegram_id = models.BigIntegerField(unique = True)
	username = models.CharField(max_length =200, null = True, blank = True)
	first_name = models.CharField(max_length=200, null = True, blank = True)
	last_name =  models.CharField(max_length=200, null = True, blank = True)
	language_code = models.CharField(max_length=10, null = True, blank = True)
	is_bot =  models.BooleanField(default = False)
	created_at = models.DateTimeField(auto_now_add = True)
	updated_at = models.DateTimeField(auto_now = True)
	is_active = models.BooleanField(default = True)
	last_interaction =models.DateTimeField(auto_now = True)

	def __str__(self):
		return f"{self.username or self.first_name or self.telegram_id}"

	class Meta:
		verbose_name = "Telegram User"
		
class UserInteraction(models.Model):
	INTERACTION_TYPES = [
		('start', 'Bot Started'),
		('message', 'Message sent'),
		('command', 'Command Used'),
		('callback', 'Callback Query'),
		('inline', 'Inline Query'),
	]

	user = models.ForeignKey(TelegramUser, on_delete= models.CASCADE, related_name = 'interaction')
	interaction_type = models.CharField(max_length = 20, choices = INTERACTION_TYPES)
	command = models.CharField(max_length = 200, null = True, blank = True)
	message_text = models.TextField(null = True, blank = True)
	callback_data = models.CharField(max_length = 200, null = True, blank = True)
	timestamp = models.DateTimeField(auto_now_add = True)
	session_id = models.CharField(max_length = 200, null = True, blank = True)
	def __str__(self):
		return f"{self.user} - {self.interaction_type} - {self.timestamp}"
	
	class Meta:
		verbose_name = "User Interaction"
		ordering = ['-timestamp']

class BotStatistics(models.Model):
	date = models.DateTimeField(unique = True)
	total_users = models.IntegerField(default = 0)
	new_users = models.IntegerField(default = 0)
	active_users = models.IntegerField(default = 0)
	total_messages = models.IntegerField(default = 0)
	total_commands = models.IntegerField(default = 0)
	created_at = models.DateTimeField(auto_now_add = True)
	updated_at = models.DateTimeField(auto_now = True)
	
	def __str__(self):
		return f"Stats for {self.date}"
	
	class Meta:
		verbose_name = "Bot Statistics"
		ordering = ['-date']

class CommandUsage(models.Model):
	command = models.CharField(max_length = 200)
	usage_count = models.IntegerField(default = 0)
	last_used = models.DateTimeField(auto_now = True)

	def __str__(self):
		return f"{self.command} - Used: {self.usage_count} times"

	class Meta:
		verbose_name = "Command Usage"
		ordering = ['-usage_count']
