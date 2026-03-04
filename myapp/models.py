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

    order_type = models.CharField(max_length=10, choices=ORDER_TYPE)
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS,
        default='PENDING'
    )
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