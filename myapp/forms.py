from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Restaurant, Order, Reservation, MenuItem, Contact


# =========================
# CADASTRO PERSONALIZADO
# =========================
class CustomUserCreationForm(UserCreationForm):

    USER_TYPE = (
        ('cliente', 'Cliente'),
        ('empresa', 'Empresa'),
    )

    user_type = forms.ChoiceField(
        choices=USER_TYPE,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label="Tipo de Conta"
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'user_type']

    def save(self, commit=True):
        user = super().save(commit)

        # 🔥 Atualiza o profile automaticamente
        user.profile.user_type = self.cleaned_data['user_type']
        user.profile.save()

        return user


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
# PEDIDO ONLINE
# =========================
class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['order_type']
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
        fields = ['date', 'time', 'number_of_people', 'observation']
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
            'observation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Possui alergia ou alguma observação?'
            }),
        }


# =========================
# FALE CONOSCO
# =========================
class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu nome'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu email'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Digite sua mensagem'
            }),
        }

# =========================
# ENDEREÇO DE ENTREGA
# =========================
class DeliveryAddressForm(forms.Form):
    delivery_address = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control-modern',
            'placeholder': 'Rua, número',
            'id': 'id_delivery_address',
        }),
        label='Endereço'
    )
    delivery_complement = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-modern',
            'placeholder': 'Apartamento, bloco (opcional)',
        }),
        label='Complemento'
    )
    delivery_neighborhood = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-modern',
            'placeholder': 'Bairro',
        }),
        label='Bairro'
    )
    delivery_city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-modern',
            'placeholder': 'Cidade',
        }),
        label='Cidade'
    )
    delivery_cep = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-modern',
            'placeholder': '00000-000',
            'id': 'id_delivery_cep',
        }),
        label='CEP'
    )
    delivery_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control-modern',
            'placeholder': '(71) 99999-9999',
        }),
        label='Telefone para entrega'
    )
