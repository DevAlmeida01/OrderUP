from django.db import models
from django.contrib.auth.models import User


# =========================
# RESTAURANTE
# =========================
class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='restaurants/', blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =========================
# CARDÁPIO DIGITAL
# =========================
class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='menu/', blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


# =========================
# PEDIDO ONLINE (CARRINHO)
# =========================
class Order(models.Model):

    ORDER_STATUS = [
        ('PENDING', 'Pendente'),
        ('PREPARING', 'Em preparo'),
        ('READY', 'Pronto'),
        ('DELIVERED', 'Entregue'),
        ('CANCELLED', 'Cancelado'),
    ]

    ORDER_TYPE = [
        ('LOCAL', 'Consumo no Local'),
        ('DELIVERY', 'Entrega'),
    ]

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ TOTAL AUTOMÁTICO (SEM BANCO)
    @property
    def total(self):
        return sum(
            item.menu_item.price * item.quantity
            for item in self.items.all()
        )

    def __str__(self):
        return f"Pedido {self.id} - {self.customer.username}"


# =========================
# ITENS DO PEDIDO
# =========================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"


# =========================
# RESERVA DE MESA
# =========================
class Reservation(models.Model):

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    number_of_people = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} - {self.restaurant.name}"