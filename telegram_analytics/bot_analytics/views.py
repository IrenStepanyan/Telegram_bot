import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from datetime import date, timedelta
from .models import TelegramUser, UserInteraction, BotStatistics
from .bot import bot_instance

@csrf_exempt
@require_POST
def webhook_view(request):
	try:
		update_data = json.loads(request.body.decode('utf-8'))
		return JsonResponse({'status': 'ok'})
	except Exception as e:
		return JsonResponse({'error': str(e)}, status = 400)


@staff_member_required
def dashboard_view(request):
	thirty_days_ago = date.today() - timedelta(days=30)
	stats = BotStatistics.objects.filter(date__gte=thirty_days_ago).order_by('date')

	top_users = TelegramUser.objects.annotate(
		interaction_count=Count('interactions')
		).order_by('-interaction_count')[:10]

	recent_interactions = UserInteraction.objects.select_related('user').order_by('-timestamp')[:20]

	context = {
		'stats': stats,
		'top_users': top_users,
		'recent_interactions': recent_interactions,
		'total_users': TelegramUser.objects.count(),
		'active_today': TelegramUser.objects.filter(last_interaction__date=date.today()).cont(),
	}
	return render(request, 'bot_analytics/dashboard.html', context)
