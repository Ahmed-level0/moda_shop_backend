from rest_framework import serializers
from coupons.serializers import CouponSerializer
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    product_price = serializers.ReadOnlyField(source='price')
    total_price = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_price', 'quantity', 'total_price', 'product_image']

    def get_product_image(self, obj):
        image = obj.product.images.first()
        if image:
            return image.image.url
        return None

    def get_total_price(self, obj):
        return obj.price * obj.quantity



class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    coupon = CouponSerializer(read_only=True)
    discount = serializers.ReadOnlyField(source='discount_amount')

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'phone', 'address', 'total_price', 'discount', 'coupon', 'created_at', 'items']
        read_only_fields = ['id', 'user', 'total_price', 'discount', 'coupon', 'created_at']