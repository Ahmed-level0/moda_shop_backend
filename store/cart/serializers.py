from rest_framework import serializers
from .models import Cart, CartItem

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_price = serializers.ReadOnlyField(source='product.final_price')
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'quantity', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price


from coupons.serializers import CouponSerializer

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    coupon = CouponSerializer(read_only=True)
    discount = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'is_active', 'created_at', 'items', 'total_price', 'coupon', 'discount']

    def get_total_price(self, obj):
        return obj.total_price

    def get_discount(self, obj):
        if obj.coupon and obj.coupon.is_valid:
            items_total = sum(item.total_price for item in obj.items.all())
            if obj.coupon.discount_type == 'percentage':
                return items_total * obj.coupon.discount / 100
            else:
                return min(obj.coupon.discount, items_total)
        return 0
