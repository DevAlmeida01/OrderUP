import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse
from dotenv import load_dotenv
import os
from groq import Groq  # Importação da API do Groq

# Modelos e Forms  app
from .models import Restaurant, Order, Reservation, MenuItem, OrderItem, Contact
from .forms import (
    CustomUserCreationForm,
    RestaurantForm,
    OrderForm,
    ReservationForm,
    MenuItemForm,
    ContactForm
)

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração da API do Grok (Groq)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# =========================
# HOME
# =========================
def home(request):
    restaurants = Restaurant.objects.all()
    return render(request, 'home.html', {'restaurants': restaurants})


# =========================
# REGISTER
# =========================
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if hasattr(user, 'profile') and user.profile.user_type == 'empresa':
                return redirect('my_dashboard')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})


# =========================
# RESTAURANTES
# =========================
@login_required
def restaurant_list(request):
    restaurants = Restaurant.objects.all()
    query = request.GET.get('q')
    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    return render(request, 'restaurant_list.html', {'restaurants': restaurants})


@login_required
def restaurant_create(request):
    if not request.user.is_superuser:
        if not hasattr(request.user, 'profile') or request.user.profile.user_type != 'empresa':
            messages.error(request, "Apenas contas EMPRESA podem cadastrar restaurantes.")
            return redirect('restaurant_list')

    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES)
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.owner = request.user
            restaurant.save()
            return redirect('restaurant_list')
    else:
        form = RestaurantForm()
    return render(request, 'restaurant_form.html', {'form': form})


@login_required
def restaurant_update(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.user != restaurant.owner and not request.user.is_superuser:
        return redirect('restaurant_list')

    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurant_detail', pk=pk)
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'restaurant_form.html', {'form': form})


@login_required
def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.user == restaurant.owner or request.user.is_superuser:
        restaurant.delete()
    return redirect('restaurant_list')


@login_required
def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.user == restaurant.owner:
        orders = Order.objects.filter(restaurant=restaurant)
        reservations = Reservation.objects.filter(restaurant=restaurant)
        menu_items = restaurant.menu_items.all()
    else:
        orders = Order.objects.filter(restaurant=restaurant, customer=request.user)
        reservations = Reservation.objects.filter(restaurant=restaurant, customer=request.user)
        menu_items = restaurant.menu_items.filter(available=True)

    return render(request, 'restaurant_detail.html', {
        'restaurant': restaurant,
        'orders': orders,
        'reservations': reservations,
        'menu_items': menu_items
    })


# =========================
# MENU (CARDÁPIO)
# =========================
@login_required
def menu_create(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.user != restaurant.owner and not request.user.is_superuser:
        return redirect('restaurant_detail', pk=restaurant.id)

    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.restaurant = restaurant
            item.save()
            return redirect('restaurant_detail', pk=restaurant.id)
    else:
        form = MenuItemForm()
    return render(request, 'menu_form.html', {'form': form, 'restaurant': restaurant})


@login_required
def menu_update(request, restaurant_id, item_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)

    if request.user != restaurant.owner and not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para editar este produto.")
        return redirect('restaurant_detail', pk=restaurant.id)

    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Produto atualizado com sucesso!")
            return redirect('restaurant_detail', pk=restaurant.id)
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'menu_form.html', {'form': form, 'restaurant': restaurant})


@login_required
def menu_delete(request, restaurant_id, item_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)

    if request.user != restaurant.owner and not request.user.is_superuser:
        return redirect('restaurant_detail', pk=restaurant.id)

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Produto excluído com sucesso!")
        return redirect('restaurant_detail', pk=restaurant.id)

    return render(request, 'menu_confirm_delete.html', {'item': item, 'restaurant': restaurant})


# =========================
# PEDIDOS
# =========================
@login_required
def order_create(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu_items = restaurant.menu_items.filter(available=True)

    if request.method == 'POST':
        items = request.POST.getlist('menu_item')
        quantities = request.POST.getlist('quantity')
        order_type = request.POST.get('order_type')

        valid_items = [
            (item_id, qty) for item_id, qty in zip(items, quantities)
            if item_id and int(qty) > 0
        ]

        if not valid_items:
            messages.error(request, "Selecione pelo menos um produto.")
            return redirect('order_create', restaurant_id=restaurant.id)

        order = Order.objects.create(
            restaurant=restaurant,
            customer=request.user,
            order_type=order_type,
            status='PENDING'
        )

        for item_id, qty in valid_items:
            menu_item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=int(qty))

        if order_type == 'DELIVERY':
            return redirect('payment_area', order_id=order.id)
        else:
            messages.success(request, 'Pedido realizado com sucesso!')
            return redirect('order_detail', pk=order.id)

    return render(request, 'order_form.html', {
        'menu_items': menu_items,
        'restaurant': restaurant,
        'form': OrderForm()
    })


@login_required
def payment_area(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.user != order.customer and request.user != order.restaurant.owner and not request.user.is_superuser:
        return redirect('restaurant_list')
    return render(request, 'payment_area.html', {'order': order})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST' and request.user == order.restaurant.owner:
        order.status = request.POST.get('status')
        order.save()
    return render(request, 'order_detail.html', {'order': order})


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    restaurant_id = order.restaurant.id
    order.delete()
    return redirect('restaurant_detail', pk=restaurant_id)


@login_required
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.method == 'POST' and request.user == order.restaurant.owner:
        order.status = request.POST.get('status')
        order.save()
    return redirect('order_detail', pk=pk)


# =========================
# RESERVAS
# =========================
@login_required
def reservation_create(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.restaurant = restaurant
            reservation.customer = request.user
            reservation.save()
            return redirect('restaurant_detail', pk=restaurant.id)
    else:
        form = ReservationForm()
    return render(request, 'reservation_form.html', {'form': form})


@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST' and request.user == reservation.restaurant.owner:
        reservation.status = request.POST.get('status')
        reservation.save()
    return render(request, 'reservation_detail.html', {'reservation': reservation})


@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    restaurant_id = reservation.restaurant.id
    reservation.delete()
    return redirect('restaurant_detail', pk=restaurant_id)


# =========================
# DASHBOARD
# =========================
@login_required
def my_dashboard(request):
    user = request.user
    if user.is_superuser:
        restaurants = Restaurant.objects.all()
        orders = Order.objects.all()
        reservations = Reservation.objects.all()
        template = 'dashboard_admin.html'
    elif hasattr(user, 'profile') and user.profile.user_type == 'empresa':
        restaurants = Restaurant.objects.filter(owner=user)
        orders = Order.objects.filter(restaurant__owner=user)
        reservations = Reservation.objects.filter(restaurant__owner=user)
        template = 'dashboard.html'
    else:
        restaurants = None
        orders = Order.objects.filter(customer=user)
        reservations = Reservation.objects.filter(customer=user)
        template = 'dashboard_cliente.html'

    total_vendas = orders.count()
    aguardando_pagamento = orders.filter(status='PENDING').count()
    total_faturado = sum(order.total for order in orders)

    return render(request, template, {
        'restaurants': restaurants,
        'orders': orders,
        'reservations': reservations,
        'total_vendas': total_vendas,
        'aguardando_pagamento': aguardando_pagamento,
        'total_faturado': total_faturado,
    })


# =========================
# CONTATO / AUXILIARES
# =========================
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


def client_company(request):
    return render(request, 'client_company.html')


# =================================
# CHAT IA (API DO GROQ - Llama 3)
# =================================
def chat_ai(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get('message')

            # Chamada para o Groq
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Você é o assistente virtual do sistema OrderUp. Ajude os clientes de forma curta e objetiva."
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
                model="llama-3.3-70b-versatile",
            )

            ai_response = chat_completion.choices[0].message.content
            return JsonResponse({'response': ai_response})
            
        except Exception as e:
            print(f"Erro Groq: {e}")
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Método inválido'}, status=400)