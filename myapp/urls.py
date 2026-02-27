from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # =========================
    # HOME / AUTH
    # =========================
    path('', views.home, name='home'),

    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.register, name='register'),

    # =========================
    # RESTAURANTES
    # =========================
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/create/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),

    # Apenas ADMIN pode editar/excluir
    path('restaurants/<int:pk>/edit/', views.restaurant_update, name='restaurant_update'),
    path('restaurants/<int:pk>/delete/', views.restaurant_delete, name='restaurant_delete'),

    # =========================
    # CARDÁPIO DIGITAL
    # =========================
    path('restaurants/<int:restaurant_id>/menu/add/', views.menu_create, name='menu_create'),

    # =========================
    # PEDIDOS
    # =========================
    path('restaurants/<int:restaurant_id>/orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),
    path('orders/<int:pk>/status/', views.order_update_status, name='order_update_status'),

    # =========================
    # RESERVAS
    # =========================
    path('restaurants/<int:restaurant_id>/reservations/create/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/delete/', views.reservation_delete, name='reservation_delete'),

    # =========================
    # PAINEL DO DONO
    # =========================
    path('dashboard/', views.my_dashboard, name='dashboard'),
]