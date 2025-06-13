#the bots logic is here

import logging 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from django.conf import settings
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import TelegramUser, UserInteraction, BotStatistics, CommandUsage
from django.db.models import F
from datetime import date

logging.basicConfig(
	format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
	#defines how each log message will look
	#asctime -> timestamp of the log 
	#%(name)s -> The name of the logger (file/modul name)
	#%(levelname)s -> (DEBUG, INFO, WARNING)
	#%(message)s ->the actual log message

	#logging.INFO -> log everything from Info level and above 
	#(Info, warning, error, critical but not debug)
)

logger = logging.getLogger(__name__)
# creats a logger specifically for the current Python file/module

class TelegramBotAnalytics:
	def __init__(self):
		self.application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
		self.setup_handlers()
	
	def setup_handlers(self):
		self.application.add_handler(CommandHandler("start", self.start_command))
		self.application.add_handler(CommandHandler("help", self.help_command))
		self.application.add_handler(CommandHandler("stats", self.stats_command))
		self.application.add_handler(CallbackQueryHandler(self.button_callback))
		self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
		#handles only plain text no command 

	@sync_to_async
	def get_or_create_user_sync(self, telegram_user_data):
		user, created = TelegramUser.objects.get_or_create(
			telegram_id = telegram_user_data['id'],
			defaults = {
				'username': telegram_user_data.get('username'),
				'first_name': telegram_user_data.get('first_name'),
				'last_name': telegram_user_data.get('last_name'),
				'language_code': telegram_user_data.get('language_code'),
				'is_bot': telegram_user_data.get('is_bot', False),
			}
		)

			
		# if there is a user with that id in our database -> user = that user in TelegramUser format + created = False 
		#if there isn't a user it creates the new own and created = True

		if not created:  #old user maybe data change 
			user.username = telegram_user_data.get('username')
			user.first_name = telegram_user_data.get('first_name')
			user.last_name = telegram_user_data.get('last_name')
			user.language_code = telegram_user_data.get('language_code')
			user.last_interaction = timezone.now()
			user.save()
			
		return user

	async def get_or_create_user(self, update: Update) -> TelegramUser:
		telegram_user = update.effective_user
		telegram_user_data = {
			'id': telegram_user.id,
			'username': telegram_user.username,
			'first_name': telegram_user.first_name,
			'last_name': telegram_user.last_name,
			'language_code': telegram_user.language_code,
			'is_bot': telegram_user.is_bot,
		}
		
		return await self.get_or_create_user_sync(telegram_user_data)


#record each user interaction in database 
	@sync_to_async
	def log_interaction_sync(self, user_id, interaction_type, **kwargs):	
		UserInteraction.objects.create(
			user_id = user_id,
			interaction_type = interaction_type,
			command = kwargs.get('command'),
			message_text = kwargs.get('message_text'),
			callback_data= kwargs.get('callback_data'),
		)

	async def log_interaction(self, user: TelegramUser, interaction_type: str, **kwargs):
		await self.log_interaction_sync(user.id, interaction_type, **kwargs)

		await self.update_daily_stats(interaction_type)
	

	@sync_to_async
	def update_daily_stats_sync(self, interaction_type):
		today = date.today()
		stats, created = BotStatistics.objects.get_or_create(
			date = today,
			defaults = {
				'total_users': TelegramUser.objects.count(),
				'new_users': TelegramUser.objects.filter(created_at__date = today).count(),
				'active_users': TelegramUser.objects.filter(last_interaction__date=today).count(),
		}

		)

		if interaction_type == 'message':
			stats.total_messages = F('total_messages')+1
		elif interaction_type == 'command':
			stats.total_commands = F('total_commands')+1
		
		stats.active_users = TelegramUser.objects.filter(last_interaction__date = today).count()
		stats.save()


	async def update_daily_stats(self, interaction_type: str):
		await self.update_daily_stats_sync(interaction_type)


	@sync_to_async 
	def update_command_usage_sync(self, command):
		cmd_usage, created = CommandUsage.objects.get_or_create(
			command = command,
			defaults = { 'usage_count': 0}
		)
		cmd_usage.usage_count = F('usage_count')+1
		cmd_usage.save()

	async def update_command_usage(self, command: str):
		await self.update_command_usage_sync(command)

	async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user = await self.get_or_create_user(update)
		await self.log_interaction(user, 'start', command = 'start')
		await self.update_command_usage('start')

		keyboard = [
			[InlineKeyboardButton("My stats", callback_data = 'my_stats')],
			[InlineKeyboardButton("Help", callback_data = 'help')],
		]
		reply_markup = InlineKeyboardMarkup(keyboard)

		welcome_text = f"Hello {user.first_name or 'there'}!\n\n"
		welcome_text += "Welcome to the Analytics Bot! I track your interactions and provide insights.\n\n"
		welcome_text += "Use the buttons below or type /help for available commands."

		await update.message.reply_text(welcome_text, reply_markup = reply_markup)

	async def help_command(self, update: Update, context = ContextTypes.DEFAULT_TYPE):
		user = await self.get_or_create_user(update)
		await self.log_interaction(user, 'command', command = 'help')
		await self.update_command_usage('help')

		help_text  = """
		*Bot Commands:*

		/start ->Starts the bot 
		/help -> Show this message
		/stats -> Show your personal statistics

		Inside the stats there is 
		- Number of messages sent
		- Commands used
		- Interaction timestamps
		- User activity patterns

		Note: Your data is used only for creating this statistics.

		"""
		if update.callback_query:
			query = update.callback_query
			await update.message.reply_text(help_text, parse_mode = "Markdown")
			await query.answer()
		else:
			await update.message.reply_text(help_text, parse_mode = "Markdown")
	@sync_to_async
	def get_user_stats_sync(self, user_id):
		user = TelegramUser.objects.get(id = user_id)
		total_interactions = user.interactions.count()
		messages_count = user.interactions.filter(interaction_type = 'message').count()
		commands_count = user.interactions.filter(interaction_type = 'command').count()

		return {
			'user': user,
			'total_interactions': total_interactions,
			'messages_count': messages_count,
			'commands_count': commands_count,
		}

	async def stats_command(self, update: Update, context = ContextTypes.DEFAULT_TYPE):
		user = await self.get_or_create_user(update)
		await self.log_interaction(user, 'command', command = 'stats')
		await self.update_command_usage('stats')

		stats_data = await self.get_user_stats_sync(user.id)	

		stats_text = f"""
		*Your Statistics:*

		*User Info*
		-Joined: {stats_data['user'].created_at.strftime('%Y-%m-%d')}
		-Last seen: {stats_data['user'].last_interaction.strftime('%Y-%m-%d %H:%M')}

		*Activity:*
		- Total Interactions: {stats_data['total_interactions']}
		- Messages sent: {stats_data['messages_count']}
		- Commands used: {stats_data['commands_count']}

		*Account info:*
		- Usage time: {(timezone.now() - stats_data['user'].created_at).days} days

		"""
		if update.callback_query:
			query = update.callback_query
			await query.message.reply_text(stats_text, parse_mode = "Markdonw")
			await query.answer()
		else:
			await update.message.reply_text(stats_text, parse_mode = 'Markdown')
		
	async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		# handles button callbacks
		
		query = update.callback_query
		user = await self.get_or_create_user(update)
		await self.log_interaction(user, 'callback', callback_data = query.data)

		if query.data == 'my_stats':
			await self.stats_command(update, context)
		elif query.data == 'help':
			await self.help_command(update, context)
		else:
			await query.message.reply_text("Unknown option selected")
			await query.answer()
		
		await query.message.reply_text("You selected option had been processed!")
	async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		#handls normal messages 
		user = await self.get_or_create_user(update)
		await self.log_interaction(
			user,
			'message',
			message_text = update.message.text[:500] #limts the message length
		)
		
		stats_data = await self.get_user_stats_sync(user.id)
		
		response = f"Thanks for your message.\n\n'"
		response += f"Message received at: {timezone.now().strftime('%H:%M:%S')}\n" 
		response += f"Your message count: {stats_data['messages_count']}"

		await update.message.reply_text(response)

#init bot instance
bot_instance = TelegramBotAnalytics()
