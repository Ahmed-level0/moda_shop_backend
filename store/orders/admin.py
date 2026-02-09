from django.contrib import admin
from .models import Order, OrderItem

# Register your models here.
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','payment_reference' ,'user', 'status', 'address', 'total_price', 'created_at')
    search_fields = ('user__username', 'payment_reference')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
