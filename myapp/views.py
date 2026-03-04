from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import login

from .models import Restaurant, Order, Reservation, MenuItem, OrderItem, Contact
from .forms import (
    CustomUserCreationForm,
    RestaurantForm,
    OrderForm,
    ReservationForm,
    MenuItemForm,
    ContactForm
)

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

            if user.profile.user_type == 'empresa':
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
            messages.error(request, "Apenas contas do tipo EMPRESA podem cadastrar restaurantes.")
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

        # 🔥 Verifica se há pelo menos um item válido
        valid_items = [
            (item_id, qty)
            for item_id, qty in zip(items, quantities)
            if item_id and int(qty) > 0
        ]

        if not valid_items:
            messages.error(request, "Você precisa selecionar pelo menos um produto válido.")
            return redirect('order_create', restaurant_id=restaurant.id)

        # 🔥 Cria pedido já como PENDING (indo para pagamento)
        order = Order.objects.create(
            restaurant=restaurant,
            customer=request.user,
            order_type=order_type,
            status='PENDING'
        )

        for item_id, qty in valid_items:
            menu_item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=int(qty)
            )

        return redirect('payment_area', order_id=order.id)

    form = OrderForm()
    return render(request, 'order_form.html', {
        'menu_items': menu_items,
        'restaurant': restaurant,
        'form': form
    })


@login_required
def payment_area(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # 🔥 Segurança
    if request.user != order.customer and request.user != order.restaurant.owner and not request.user.is_superuser:
        return redirect('restaurant_list')

    return render(request, 'payment_area.html', {
        'order': order
    })


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
        template = 'dashboard_empresa.html'

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