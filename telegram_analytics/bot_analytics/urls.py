from django.urls import path
from . import views

app_name = 'bot_analytics'

urlpatterns = [
	path('webhook/', views.webhook_view, name = 'webhook'),
	path('dashboard/', views.dashboard_view, name = 'dashboard'),
]
	
