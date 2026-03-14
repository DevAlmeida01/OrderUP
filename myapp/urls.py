from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # =========================
    # HOME / AUTENTICAÇÃO
    # =========================
    path('', views.home, name='home'),

    path('login/', auth_views.LoginView.as_view(
        template_name='auth/login.html',
        redirect_authenticated_user=True
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),

    path('register/', views.register, name='register'),

    # =========================
    # RESTAURANTES
    # =========================
    path('restaurants/', views.restaurant_list, name='restaurant_list'),
    path('restaurants/create/', views.restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/', views.restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:pk>/edit/', views.restaurant_update, name='restaurant_update'),
    path('restaurants/<int:pk>/delete/', views.restaurant_delete, name='restaurant_delete'),

    # =========================
    # CARDÁPIO
    # =========================
    path(
        'restaurants/<int:restaurant_id>/menu/add/',
        views.menu_create,
        name='menu_create'
    ),

    path(
        'restaurants/<int:restaurant_id>/menu/<int:item_id>/edit/',
        views.menu_update,
        name='menu_update'
    ),

    path(
        'restaurants/<int:restaurant_id>/menu/<int:item_id>/delete/',
        views.menu_delete,
        name='menu_delete'
    ),

    # =========================
    # PEDIDOS
    # =========================
    path(
        'restaurants/<int:restaurant_id>/orders/create/',
        views.order_create,
        name='order_create'
    ),

    path(
        'pedido/<int:order_id>/pagamento/',
        views.payment_area,
        name='payment_area'
    ),

    path(
        'orders/<int:pk>/',
        views.order_detail,
        name='order_detail'
    ),

    path(
        'orders/<int:pk>/delete/',
        views.order_delete,
        name='order_delete'
    ),

    path(
        'orders/<int:pk>/status/',
        views.order_update_status,
        name='order_update_status'
    ),

    # =========================
    # RESERVAS
    # =========================
    path(
        'restaurants/<int:restaurant_id>/reservations/create/',
        views.reservation_create,
        name='reservation_create'
    ),

    path(
        'reservations/<int:pk>/',
        views.reservation_detail,
        name='reservation_detail'
    ),

    path(
        'reservations/<int:pk>/delete/',
        views.reservation_delete,
        name='reservation_delete'
    ),

    # =========================
    # DASHBOARD E UTILITÁRIOS
    # =========================
    path('dashboard/', views.my_dashboard, name='my_dashboard'),
    path('contact/', views.contact_view, name='contact'),
    path('cliente-empresa/', views.client_company, name='client_company'),

    # =========================
    # CHAT IA (NOVA ROTA)
    # =========================
    path('chat-ai/', views.chat_ai, name='chat_ai'),
]