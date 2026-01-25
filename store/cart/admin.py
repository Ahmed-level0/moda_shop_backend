from django.contrib import admin
from .models import Cart, CartItem
# Register your models here.

# admin.site.register(Cart)
# admin.site.register(CartItem)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'is_active', 'total_price')
    list_filter = ('is_active', 'created_at',)
    search_fields = ('user__username', 'id')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'total_price')
    list_filter = ('cart__is_active', 'product__name',)
    search_fields = ('product__name', 'cart__user__username')
    readonly_fields = ('total_price',)
