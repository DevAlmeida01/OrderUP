from django import forms
from .models import Restaurant, Order, Reservation, MenuItem


# =========================
# RESTAURANTE
# =========================
class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do restaurante'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descreva o restaurante...'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }


# =========================
# CARDÁPIO DIGITAL
# =========================
class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'image', 'available']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do item'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição do item'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preço'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


# =========================
# PEDIDO ONLINE (ATUALIZADO)
# =========================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_type']  # 🔥 removidos menu_item e quantity
        widgets = {
            'order_type': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


# =========================
# RESERVA DE MESA
# =========================
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['date', 'time', 'number_of_people']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'number_of_people': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Número de pessoas'
            }),
        }