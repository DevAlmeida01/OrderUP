from django.contrib import admin
from .models import Profile, Restaurant, MenuItem, Order, OrderItem, Reservation, Contact, OrderStatusLog, RestaurantSettings


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_type')
    list_filter = ('user_type',)
    search_fields = ('user__username',)


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0
    fields = ('name', 'price', 'available')


class RestaurantSettingsInline(admin.StackedInline):
    model = RestaurantSettings
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'owner__username')
    inlines = [MenuItemInline, RestaurantSettingsInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price', 'available')
    list_filter = ('available', 'restaurant')
    list_editable = ('available', 'price')
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'quantity')


class StatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'changed_by', 'message', 'created_at')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'restaurant', 'order_type', 'status', 'total_display', 'payment_method', 'created_at')
    list_filter = ('status', 'order_type', 'payment_method')
    search_fields = ('customer__username', 'restaurant__name')
    list_editable = ('status',)
    readonly_fields = ('paid_at', 'payment_id', 'last_status_update', 'created_at')
    inlines = [OrderItemInline, StatusLogInline]

    def total_display(self, obj):
        return f'R$ {obj.total:.2f}'
    total_display.short_description = 'Total'


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status',)
    readonly_fields = ('created_at',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'restaurant', 'date', 'time', 'number_of_people')
    list_filter = ('date', 'restaurant')
    search_fields = ('customer__username', 'restaurant__name')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = ('restaurant', 'delivery_fee', 'estimated_delivery_minutes', 'accepts_delivery')
    list_editable = ('delivery_fee', 'accepts_delivery')
