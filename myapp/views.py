from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import Restaurant, Order, Reservation, MenuItem, OrderItem
from .forms import RestaurantForm, OrderForm, ReservationForm, MenuItemForm


# =========================
# HOME
# =========================

def home(request):
    restaurants = Restaurant.objects.all().order_by('-id')
    return render(request, 'home.html', {'restaurants': restaurants})


# =========================
# REGISTER
# =========================

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'auth/register.html', {'form': form})


# =========================
# LISTA RESTAURANTES
# =========================

@login_required
def restaurant_list(request):
    restaurants = Restaurant.objects.all().order_by('-id')

    query = request.GET.get('q')
    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )

    restaurants = restaurants.select_related('owner')

    return render(request, 'restaurant_list.html', {
        'restaurants': restaurants
    })


# =========================
# CRIAR RESTAURANTE
# =========================

@login_required
def restaurant_create(request):
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


# =========================
# DETALHE RESTAURANTE
# =========================

@login_required
def restaurant_detail(request, pk):
    restaurant = get_object_or_404(
        Restaurant.objects.select_related('owner'),
        pk=pk
    )

    menu_items = MenuItem.objects.filter(
        restaurant=restaurant,
        available=True
    )

    if request.user == restaurant.owner:
        orders = Order.objects.filter(
            restaurant=restaurant
        ).select_related('customer').order_by('-created_at')

        reservations = Reservation.objects.filter(
            restaurant=restaurant
        ).select_related('customer').order_by('-created_at')
    else:
        orders = Order.objects.filter(
            restaurant=restaurant,
            customer=request.user
        ).select_related('customer')

        reservations = Reservation.objects.filter(
            restaurant=restaurant,
            customer=request.user
        ).select_related('customer')

    return render(request, 'restaurant_detail.html', {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'orders': orders,
        'reservations': reservations
    })


# =========================
# EDITAR RESTAURANTE (SÓ ADMIN)
# =========================

@login_required
def restaurant_update(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)

    if not request.user.is_superuser:
        return redirect('restaurant_list')

    if request.method == 'POST':
        form = RestaurantForm(request.POST, request.FILES, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect('restaurant_list')
    else:
        form = RestaurantForm(instance=restaurant)

    return render(request, 'restaurant_form.html', {'form': form})


# =========================
# DELETAR RESTAURANTE (SÓ ADMIN)
# =========================

@login_required
def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)

    if not request.user.is_superuser:
        return redirect('restaurant_list')

    if request.method == 'POST':
        restaurant.delete()
        return redirect('restaurant_list')

    return render(request, 'restaurant_confirm_delete.html', {'restaurant': restaurant})


# =========================
# ADICIONAR ITEM AO CARDÁPIO (SÓ DONO)
# =========================

@login_required
def menu_create(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.user != restaurant.owner:
        return redirect('restaurant_list')

    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            menu_item = form.save(commit=False)
            menu_item.restaurant = restaurant
            menu_item.save()
            return redirect('restaurant_detail', pk=restaurant.id)
    else:
        form = MenuItemForm()

    return render(request, 'menu_form.html', {'form': form})


# =========================
# CRIAR PEDIDO (COM TOTAL)
# =========================

@login_required
def order_create(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    menu_items = MenuItem.objects.filter(
        restaurant=restaurant,
        available=True
    )

    if request.method == 'POST':
        order_type = request.POST.get('order_type')

        if not order_type:
            return redirect('restaurant_list')

        order = Order.objects.create(
            restaurant=restaurant,
            customer=request.user,
            order_type=order_type,
            total=0  # inicia zerado
        )

        items = request.POST.getlist('menu_item')
        quantities = request.POST.getlist('quantity')

        total = 0  # 🔥 NOVO

        for item_id, qty in zip(items, quantities):
            if item_id and qty:
                menu_item = MenuItem.objects.get(id=item_id)

                if menu_item.restaurant != restaurant:
                    continue

                qty = int(qty)

                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=qty
                )

                total += menu_item.price * qty  # 🔥 SOMA

        order.total = total  # 🔥 SALVA TOTAL
        order.save()

        return redirect('restaurant_detail', pk=restaurant.id)

    return render(request, 'order_form.html', {
        'menu_items': menu_items,
        'form': OrderForm()
    })


# =========================
# ALTERAR STATUS PEDIDO (SÓ DONO)
# =========================

@login_required
def order_update_status(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('restaurant'),
        pk=pk
    )

    if request.user != order.restaurant.owner:
        return redirect('restaurant_list')

    new_status = request.POST.get('status')

    if new_status:
        order.status = new_status
        order.save()

    return redirect('restaurant_detail', pk=order.restaurant.id)


# =========================
# CRIAR RESERVA
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


# =========================
# DASHBOARD DO DONO
# =========================

@login_required
def my_dashboard(request):
    restaurants = Restaurant.objects.filter(
        owner=request.user
    )

    orders = Order.objects.filter(
        restaurant__owner=request.user
    ).select_related('restaurant', 'customer').order_by('-created_at')

    reservations = Reservation.objects.filter(
        restaurant__owner=request.user
    ).select_related('restaurant', 'customer').order_by('-created_at')

    return render(request, 'dashboard.html', {
        'restaurants': restaurants,
        'orders': orders,
        'reservations': reservations
    })


# =========================
# DELETAR PEDIDO
# =========================

@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if request.user != order.restaurant.owner and request.user != order.customer:
        return redirect('restaurant_list')

    restaurant_id = order.restaurant.id

    if request.method == 'POST':
        order.delete()
        return redirect('restaurant_detail', pk=restaurant_id)

    return render(request, 'order_confirm_delete.html', {'order': order})


# =========================
# DELETAR RESERVA
# =========================

@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)

    if request.user != reservation.restaurant.owner and request.user != reservation.customer:
        return redirect('restaurant_list')

    restaurant_id = reservation.restaurant.id

    if request.method == 'POST':
        reservation.delete()
        return redirect('restaurant_detail', pk=restaurant_id)

    return render(request, 'reservation_confirm_delete.html', {'reservation': reservation})