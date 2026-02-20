from rest_framework import serializers
from .models import Coupon

class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount', 'discount_type', 'active', 
            'valid_from', 'valid_until', 'usage_limit', 'usage_count', 'is_valid'
        ]