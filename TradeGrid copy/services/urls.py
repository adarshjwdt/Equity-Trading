from django.urls import path
from . import views

urlpatterns = [
    path('sync/', views.sync_all_accounts, name='sync_all'),
    path('live-prices/', views.get_live_prices, name='live_prices'),
    path('kite-login/', views.kite_login, name='kite_login'),
    path('kite-callback/', views.kite_callback, name='kite_callback'),
]