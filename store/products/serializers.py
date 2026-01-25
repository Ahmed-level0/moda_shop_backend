from rest_framework import serializers
from .models import Product, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = ProductImage
        fields = ['id', 'image']

# Serializer for Product model
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True) # Nested serializer for product images
    final_price = serializers.SerializerMethodField() # Custom field to calculate final price after discount

    class Meta:
        # Specify the model and fields to be serialized
        model = Product
        fields = '__all__'

    def get_final_price(self, obj):
        if obj.discount:
            return obj.price - (obj.price * obj.discount / 100)
        return obj.price
    
