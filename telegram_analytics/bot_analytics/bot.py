#the bots logic is here

import logging 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from django.conf import settings
from django.utils import timezone
from .models import TelegramUser, UserInteraction, BotStatistics, CommandUsage
from django.db.models import F
from datetime import date

logging.basicConfid(
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
		self.setuu_handlers()
	
	def setup_handlers(self):
		self.application.add_handler(CommandHandler("start", self.start_command))
		self.application.add_handler(CommandHandler("help", self.help_command))
		self.application.add_handler(CommandHandler("stats", self.stats_command))
		self.application.add_handler(CallbackQueryHandler(self.button_callback))
		self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
		#handles only plain text no command 

	async def get_or_create_user(self, update: Update) -> TelegramUser:
		telegram_user = update.effective_user
		user, created = TelegramUser.objects.get_or_create(
			telegram_id = telegram_user.id,
			defaults = {
					'username': telegram_user.username,
					'first_name': telegram_user.first_name,
					'last_name': telegram_user.last_name,
					'language_code': telegram_user.language_code,
					'is_bot': telegram_user.is_bot,
					}
		)
		# if there is a user with that id in our database -> user = that user in TelegramUser format + created = False 
		#if there isn't a user it creates the new own and created = True

		if not created: #old user maybe data change 
			user.username = telegram_user.username,
			user.first_name = telegram_user.first_name
			user.last_name = telegram_user.last_name
			user.language_code = telegram_user.language_code
			user.lest_interaction = timezone,now()
			user.save()
		
		return user


#record each user interaction in database 
	async def log_interaction(self, user: TelegramUser, interaction_type: str, **kwargs):
		UserInteraction.objects.create(
			user = user,
			interaction_type = interaction_type,
			command = kwargs.get('command'),
			message_text = kwargs.get('message_text'),
			callback_data= kwargs.get('callback_data'),
		)

		await self.update_daily_stats(interaction_type)
	
	async def update_daily_stats(self, interaction_type: str):
		#Updates daily statistics
		today = date.today()
		stats, created = BotStatistics.objects.get_or_creat(
			date = today,
			defaults = {
					'total_users': TelegramUser.objects.count(),
					'new_users': TelegramUser.objects.filter(created_at__date = today).count(),
					'active_users': TelegramUser.objects.filter(last_interaction_date=today)
			}
		)

		if interaction_type == 'message':
			stats.total_messages = F('total_messages')+1
		elif interaction_type == 'command':
			stats.total_commands = F('total_commands')+1
		
		stats.active_users = TelegramUser.objects.filter(last_interaction__date = today).count()
		stats.save()
	
	async def update_command_usage(self, command: str):
		cmd_usage, created = CommandUsage.objects.get_or_create(
			command = command,
			defaults = { 'usage_count': 0}
		)
		cmd_usage.usage_count = F('usage_count')+1
		cmd_usage.save()

	async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
		user = await self.get_or_create_user(update)
		await self.log_interaction(user, 'start', command = 'start')
		awair self.update_command_usage('start')

		keyboard = [
			[InlineKeyboardButton("My stats", callback_data = 'my_stats')],
			[InlineKeyboardButton("Help", callback_data = 'help')],
		]
		reply_markup = InlineKeyboardMarkup(keyboard)

		welcome_text = f"Hello {user.first_name or 'there'}!\n\n"
		welcome_text += "Welcome to the Analytics Bot! I track your interactions and provide insights.\n\n"
		welcome_text += "Use the buttons below or type /help for available commands."

		await update.message.repy_text(welcome_text, reply_markup = reply_markup)

	async def help_command(self, update: Update, context = ContextType.DEFAULT_TYPE):
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
		await update.message.reply_text(help_text, parse_mode = "Markdown")
	
	async def stats_command(self, update: Update, context = ContextType = DEFAULT_TYPE):
		user = await self.get_or_create_user(update)
		await self.log_interaction(user, 'command', command = 'stats')
		awair self.update_command_usage('stats')

		total_interactions = user.interactions.count()
		messages_count = user.interactions.filter(interaction_type= 'message').count()
		commands_count = user.interactions.filter(interaction_type = 'command').count()

		stats_text = f"""
		*Your Statistics:*

		*User Info*
		-Joined: {user.created_at.strftime('%Y-%m-%d')}
		-Last seen: {user.last_interaction.strftime('%Y-%m-%d %H:%M')}

		*Activity:*
		- Total Interactions: {total_interactions}
		- Messages sent: {messages_count}
		- Commands used: {commands_count}

		*Account info:*
		- Usage time: {(timezone.now() - user.created_at).days} days

		"""

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

		awair query.answer()

	async def handle_message(self, update: Update, context: ContextType.DEFAULT_TYPE):
		#handls normal messages 
		user = await self.get_or_create_user(update)
		await self.log_interaction(
			user,
			'message',
			message_text = update.message.text[:500] #limts the message length
		)

		response = f"Thanks for your message.\n\n'"
		response += f"Message received at: {timezone.now().strftime('%H:%M:%S')}\n" 
		response += f"Your message count: {user.interactions.filter(interaction_type='message').count()}"

		awair update.message.reply_text(response)

#init bot instance
bot_instance = TelegramBotAnalytics()
