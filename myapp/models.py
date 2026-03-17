from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import uuid
import os


# =========================
# PERFIL (CLIENTE / EMPRESA / ADMIN)
# =========================

class Profile(models.Model):
    USER_TYPE = (
        ('cliente', 'Cliente'),
        ('empresa', 'Empresa'),
        ('admin', 'Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE,
        default='cliente'
    )

    def __str__(self):
        return f"{self.user.username} ({self.user_type})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


# =========================
# RESTAURANTE
# =========================

class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if not self.owner_id:
            return

        if self.owner.is_superuser:
            return

        if not hasattr(self.owner, 'profile') or self.owner.profile.user_type != 'empresa':
            raise ValidationError(
                "Apenas usuários do tipo EMPRESA podem cadastrar restaurantes."
            )

    def __str__(self):
        return self.name


# =========================
# FUNÇÃO PARA NOMEAR IMAGEM DO MENU (🔥 CORREÇÃO)
# =========================

def menu_image_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("menu", filename)


# =========================
# CARDÁPIO DIGITAL
# =========================

class MenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)

    # 🔥 ALTERAÇÃO AQUI
    image = models.ImageField(
        upload_to=menu_image_path,
        blank=True,
        null=True
    )

    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


# =========================
# PEDIDO ONLINE
# =========================

class Order(models.Model):

    ORDER_STATUS = [
        ('PENDING', 'Aguardando pagamento'),
        ('PAID', 'Pago'),
        ('PREPARING', 'Em preparo'),
        ('READY', 'Pronto'),
        ('DELIVERED', 'Entregue'),
        ('CANCELLED', 'Cancelado'),
    ]

    ORDER_TYPE = [
        ('LOCAL', 'Consumo no Local'),
        ('DELIVERY', 'Entrega'),
    ]

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    PAYMENT_METHOD = [
        ('pix', 'PIX'),
        ('credito', 'Cartão de Crédito'),
        ('debito', 'Cartão de Débito'),
        ('dinheiro', 'Dinheiro'),
    ]

    order_type = models.CharField(max_length=10, choices=ORDER_TYPE)
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='PENDING'
    )

    # Endereço de entrega
    delivery_address = models.CharField(max_length=300, blank=True, null=True)
    delivery_complement = models.CharField(max_length=100, blank=True, null=True)
    delivery_neighborhood = models.CharField(max_length=100, blank=True, null=True)
    delivery_city = models.CharField(max_length=100, blank=True, null=True)
    delivery_cep = models.CharField(max_length=10, blank=True, null=True)
    delivery_phone = models.CharField(max_length=20, blank=True, null=True)

    # Pagamento
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, blank=True, null=True)
    payment_id = models.CharField(max_length=200, blank=True, null=True)  # ID do MercadoPago
    paid_at = models.DateTimeField(null=True, blank=True)

    # Notificações
    customer_notified = models.BooleanField(default=False)
    last_status_update = models.DateTimeField(auto_now=True)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total(self):
        return sum(
            (item.menu_item.price * item.quantity)
            for item in self.items.all()
        ) or 0

    def __str__(self):
        return f"Pedido {self.id} - {self.customer.username}"


# =========================
# ITENS DO PEDIDO
# =========================

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"


# =========================
# RESERVA DE MESA
# =========================

class Reservation(models.Model):

    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='reservations'
    )

    customer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations'
    )

    date = models.DateField()
    time = models.TimeField()
    number_of_people = models.PositiveIntegerField()
    observation = models.TextField(blank=True, null=True)

    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reservation_link'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.restaurant.name}"


# =========================
# FALE CONOSCO
# =========================

class Contact(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

# =========================
# HISTÓRICO DE STATUS DO PEDIDO
# =========================

class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Pedido #{self.order.id}: {self.old_status} → {self.new_status}"


# =========================
# CONFIGURAÇÃO DE EMAIL DO RESTAURANTE
# =========================

class RestaurantSettings(models.Model):
    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='settings')
    notification_email = models.EmailField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    delivery_radius_km = models.DecimalField(max_digits=5, decimal_places=1, default=5.0)
    min_order_value = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    estimated_delivery_minutes = models.PositiveIntegerField(default=45)
    accepts_delivery = models.BooleanField(default=True)
    accepts_local = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Configurações do Restaurante'

    def __str__(self):
        return f"Config — {self.restaurant.name}"
