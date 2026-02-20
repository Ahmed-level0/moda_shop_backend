from django.contrib import admin
from .models import Coupon
# Register your models here.

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'discount', 'discount_type', 'valid_from', 'valid_until', 'usage_limit')
    list_filter = ('discount_type',)
    search_fields = ('code', 'id')