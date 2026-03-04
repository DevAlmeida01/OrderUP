from django.contrib import admin
from .models import Restaurant, Order, Reservation, MenuItem

admin.site.register(Restaurant)
admin.site.register(Order)
admin.site.register(Reservation)
admin.site.register = ("MenuItem")