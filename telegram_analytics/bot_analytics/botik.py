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
	format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level = logging.INFO
	)

logger = logger.getLogger(__name__)

class TelegramBotAnalytics:
	def __init__(self):
		self.appl
