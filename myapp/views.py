import json
import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from dotenv import load_dotenv

from .models import Restaurant, Order, Reservation, MenuItem, OrderItem, Contact, OrderStatusLog
from .forms import (
    CustomUserCreationForm,
    RestaurantForm,
    OrderForm,
    ReservationForm,
    MenuItemForm,
    ContactForm,
    DeliveryAddressForm,
)
from .email_service import EmailService
from .payment_service import PaymentService

load_dotenv()

logger = logging.getLogger(__name__)

# Groq client
try:
    from groq import Groq
    _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception:
    _groq_client = None

client = _groq_client

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

        # Endereço de entrega
        delivery_address = None
        if order_type == 'DELIVERY':
            delivery_address = request.POST.get('delivery_address', '').strip()
            if not delivery_address:
                messages.error(request, 'Informe o endereço de entrega.')
                return redirect('order_create', restaurant_id=restaurant.id)

        order = Order.objects.create(
            restaurant=restaurant,
            customer=request.user,
            order_type=order_type,
            status='PENDING',
            delivery_address=delivery_address,
            delivery_complement=request.POST.get('delivery_complement', ''),
            delivery_neighborhood=request.POST.get('delivery_neighborhood', ''),
            delivery_city=request.POST.get('delivery_city', ''),
            delivery_cep=request.POST.get('delivery_cep', ''),
            delivery_phone=request.POST.get('delivery_phone', ''),
        )

        for item_id, qty in valid_items:
            menu_item = get_object_or_404(MenuItem, id=item_id, restaurant=restaurant)
            OrderItem.objects.create(order=order, menu_item=menu_item, quantity=int(qty))

        # Log de criação
        OrderStatusLog.objects.create(
            order=order,
            old_status='',
            new_status='PENDING',
            changed_by=request.user,
            message='Pedido criado'
        )

        # Notificações por email
        try:
            EmailService.order_confirmed(order)
            EmailService.new_order_to_restaurant(order)
        except Exception as e:
            logger.error(f'Erro ao enviar email de confirmação: {e}')

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

    # Gera preferência no MercadoPago se token configurado
    mp_data = None
    mp_configured = bool(getattr(import_settings(), 'MERCADOPAGO_ACCESS_TOKEN', ''))
    if mp_configured and order.status == 'PENDING':
        try:
            mp_data = PaymentService.create_preference(order, request)
        except Exception as e:
            logger.error(f'Erro MercadoPago: {e}')

    return render(request, 'payment_area.html', {
        'order': order,
        'mp_data': mp_data,
        'mp_configured': mp_configured,
        'mp_public_key': getattr(import_settings(), 'MERCADOPAGO_PUBLIC_KEY', ''),
    })


def import_settings():
    from django.conf import settings
    return settings


# ── CALLBACKS MERCADOPAGO ─────────────────────────────────────────────
@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    payment_id = request.GET.get('payment_id', '')
    collection_status = request.GET.get('collection_status', '')

    if collection_status == 'approved':
        old_status = order.status
        order.status = 'PAID'
        order.payment_id = payment_id
        order.paid_at = timezone.now()
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            old_status=old_status,
            new_status='PAID',
            message=f'Pagamento aprovado via MercadoPago. ID: {payment_id}'
        )
        try:
            EmailService.order_status_changed(order, old_status)
        except Exception:
            pass
        messages.success(request, '✅ Pagamento aprovado! Seu pedido está confirmado.')
    else:
        messages.warning(request, 'Pagamento pendente. Aguardando confirmação.')

    return redirect('order_detail', pk=order.id)


@login_required
def payment_failure(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    messages.error(request, '❌ Pagamento recusado. Tente novamente ou escolha outro método.')
    return redirect('payment_area', order_id=order.id)


@login_required
def payment_pending(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    messages.info(request, '⏳ Pagamento pendente. Você receberá um email quando for confirmado.')
    return redirect('order_detail', pk=order.id)


@csrf_exempt
def mercadopago_webhook(request):
    """Webhook do MercadoPago para notificações assíncronas de pagamento."""
    if request.method != 'POST':
        return JsonResponse({'status': 'ok'})
    try:
        data = json.loads(request.body)
        topic = data.get('type') or request.GET.get('topic', '')

        if topic == 'payment':
            payment_id = data.get('data', {}).get('id') or request.GET.get('id')
            if payment_id:
                payment_info = PaymentService.get_payment_info(str(payment_id))
                external_ref = payment_info.get('external_reference')
                status_mp = payment_info.get('status')

                if external_ref and status_mp == 'approved':
                    try:
                        order = Order.objects.get(id=int(external_ref))
                        if order.status == 'PENDING':
                            old_status = order.status
                            order.status = 'PAID'
                            order.payment_id = str(payment_id)
                            order.paid_at = timezone.now()
                            order.save()
                            OrderStatusLog.objects.create(
                                order=order,
                                old_status=old_status,
                                new_status='PAID',
                                message=f'Aprovado via webhook MP. ID: {payment_id}'
                            )
                            EmailService.order_status_changed(order, old_status)
                    except Order.DoesNotExist:
                        pass
    except Exception as e:
        logger.error(f'Erro webhook MP: {e}')

    return JsonResponse({'status': 'ok'})


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
    if request.method == 'POST' and (request.user == order.restaurant.owner or request.user.is_superuser):
        old_status = order.status
        new_status_val = request.POST.get('status')

        if old_status != new_status_val:
            order.status = new_status_val
            if new_status_val == 'PAID':
                order.paid_at = timezone.now()
            order.last_status_update = timezone.now()
            order.save()

            # Registrar histórico
            OrderStatusLog.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status_val,
                changed_by=request.user,
                message=f'Status atualizado por {request.user.username}'
            )

            # Notificar cliente por email
            try:
                EmailService.order_status_changed(order, old_status)
            except Exception as e:
                logger.error(f'Erro ao enviar email de status: {e}')

            messages.success(request, f'Status atualizado para: {order.get_status_display()}')

    # Suporte HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'partials/order_status_badge.html', {'order': order})

    return redirect('order_detail', pk=pk)


# ── STATUS EM TEMPO REAL (HTMX POLLING) ──────────────────────────────
@login_required
def order_status_check(request, pk):
    """
    Endpoint para o HTMX fazer polling e atualizar o badge de status.
    O cliente consulta a cada 10 segundos para ver se o status mudou.
    """
    order = get_object_or_404(Order, pk=pk)
    if request.user != order.customer and request.user != order.restaurant.owner and not request.user.is_superuser:
        return JsonResponse({'error': 'forbidden'}, status=403)

    return render(request, 'partials/order_status_badge.html', {'order': order})


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


# ===============================================
# CHAT IA INTELIGENTE (GROQ + CONTEXTO DO BANCO)
# ===============================================
def chat_ai(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get('message')

            # --- BUSCA DADOS REAIS DO BANCO PARA O CONTEXTO ---
            all_restaurants = Restaurant.objects.all()
            db_context = "Aqui estão os restaurantes e pratos disponíveis no OrderUp:\n"
            
            for res in all_restaurants:
                db_context += f"- Restaurante: {res.name}. Especialidade: {res.description}.\n"
                items = MenuItem.objects.filter(restaurant=res, available=True)[:3]
                if items:
                    pratos = ", ".join([i.name for i in items])
                    db_context += f"  Pratos populares: {pratos}.\n"

            # --- CHAMADA PARA O GROQ COM PROMPT DE SISTEMA ---
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"Você é o assistente virtual do OrderUp. {db_context}\nInstruções: Seja simpático, use emojis e baseie suas sugestões apenas nos dados acima."
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
            print(f"Erro Chat IA: {e}")
            return JsonResponse({'error': 'Erro no processamento'}, status=500)
            
    return JsonResponse({'error': 'Acesso negado'}, status=400)