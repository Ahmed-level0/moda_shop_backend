from django.shortcuts import render
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Product
from .serializers import ProductSerializer

# Create your views here.

# API view to list all products
class ProductListAPIView(ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        
        # Apply filters based on query parameters
        if self.request.GET.get('discounted') == 'true':
            queryset = queryset.filter(discount__gt=0)

        if self.request.GET.get('in_stock') == 'true':
            queryset = queryset.filter(stock__gt=0)

        if self.request.GET.get('style'):
            queryset = queryset.filter(style=self.request.GET.get('style'))

        if self.request.GET.get('color'):
            queryset = queryset.filter(color=self.request.GET.get('color'))

        if self.request.GET.get('size'):
            queryset = queryset.filter(size=self.request.GET.get('size'))

        if self.request.GET.get('material'):
            queryset = queryset.filter(material=self.request.GET.get('material'))

        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)

        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand_id=brand)

        return queryset

    
# API view to retrieve a single product by its ID
class ProductDetailAPIView(RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
