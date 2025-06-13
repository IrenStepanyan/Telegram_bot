from django.contrib import admin
from django.db.models import Count, Q
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import TelegramUser, UserInteraction, BotStatistics, CommandUsage

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
	list_display = ['telegram_id', 'username', 'first_name', 'last_name', 'is_active', 'interaction_count', 'last_interaction', 'created_at']
	list_filter = ['is_active', 'created_at', 'last_interaction', 'language_code']
	search_fields = ['username', 'first_name', 'last_name', 'telegram_id']
	readonly_fields = ['telegram_id', 'created_at', 'updated_at']
	list_per_page = 50 #how many users to show per page


	def interaction_count(self, obj):
		count = obj.interactions.count()
		url = reverse('admin:bot_analytics_userinteraction_changelist')+ f'?user__id__exact={obj.id}'
		return format_html('<a href = "{}">{} interactions</a>', url, count)
	#top -> creates a clikable link (ex: 12 interactions -> click ->new page
	
	interaction_count.short_description = 'Interactions'
	#set the column name (shown in admin table) to Interactions


	def get_queryset(self, request):
		queryset = super().get_queryset(request) #get default list of TelegramUser record 

		return queryset.annotate(
			interaction_count = Count('interactions')
		)

		#.annotate() -> adds an additional field to each record in the queryset
		#Count() > .count() ->bc of SQL aggregation on a single query


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
	list_display = ['user', 'interaction_type', 'command', 'timestamp', 'message_preview']
	list_filter = ['interaction_type', 'timestamp', 'command']
	search_fields = ['user_username', 'user_first_name', 'command', 'message_text']
	readonly_fields = ['timestamp']
	date_hierarchy = 'timestamp'
	list_per_page = 100

	def message_preview(self, obj):
		if obj.message_text:
			return obj.message_text[:50]+"..." if len(obj.message_text)>50 else obj.message_text
		return '-'
	message_preview.short_description = 'Message Preview'

@admin.register(BotStatistics)
class BotStatisticsAdmin(admin.ModelAdmin):
	list_display = ['date', 'total_users', 'new_users', 'active_users', 'total_messages', 'total_commands']
	list_filter = ['date']
	readonly_fields = ['created_at', 'updated_at']
	date_hierarchy = 'date'

	def changelist_view(self, request, extra_context = None):
		extra_context = extra_context or {}

		week_ago = timezone.now().date() - timedelta(days=7)
		recent_stats = BotStatistics.objects.filter(date__gte = week_ago)

		if recent_stats.exists():
			extra_context['summary'] = {
				'total_users_week': sum(stat.total_users for stat in recent_stats),
				'new_users_week': sum(stat.new_users for stat in recent_stats),
				'active_users_week': sum(stat.active_users for stat in recent_stats),
				'total_messages_week': sum(stat.total_messages for stat in recent_stats),
			}
		return super().changelist_view(request, extra_context = extra_context)

@admin.register(CommandUsage)
class CommandUsageAdmin(admin.ModelAdmin):
	list_display = ['command', 'usage_count', 'last_used']
	list_filter = ['last_used']
	search_fields = ['command']
	readonly_fields = ['last_used']

	def changelist_view(self, request, extra_context = None):
		extra_context = extra_context or {}

		top_commands = CommandUsage.objects.order_by('-usage_count')[:10]
		extra_context['chart_data'] = {
			'labels': [cmd.command for cmd in top_commands],
			'data': [cmd.usage_count for cmd in top_commands]
		}

		return super().changelist_view(request, extra_context= extra_context)

admin.site.site_header = "Telegram Bot Analytics"
admin.site.site_title = "Bot Analytics Admin"
admin.site.index_title = "Welcome to Bot Analytics Administation"
	
