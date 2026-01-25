from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer, CartItemSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_active_cart(self, user):
        cart, created = Cart.objects.get_or_create(user=user, is_active=True)
        return cart

    def list(self, request):
        cart = self.get_active_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = self.get_active_cart(request.user)
        if not cart.is_active:
            return Response({"error": "Cannot add items to inactive cart"}, status=400)

        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id)

        if not product.in_stock:
            return Response({"error": "Product out of stock"}, status=400)

        # Update quantity if item exists
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response(CartSerializer(cart).data, status=200)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = self.get_active_cart(request.user)
        product_id = request.data.get('product')
        item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
        item.delete()
        return Response(CartSerializer(cart).data, status=200)

    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        cart = self.get_active_cart(request.user)
        product_id = request.data.get('product')
        quantity = int(request.data.get('quantity', 1))
        item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()
        return Response(CartSerializer(cart).data, status=200)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        cart = self.get_active_cart(request.user)
        if cart.items.count() == 0:
            return Response({"error": "Cannot checkout empty cart"}, status=400)

        with transaction.atomic():
            # Reduce stock
            for item in cart.items.all():
                if item.quantity > item.product.stock:
                    return Response(
                        {"error": f"Not enough stock for {item.product.name}"},
                        status=400
                    )
                item.product.stock -= item.quantity
                item.product.save()

            cart.is_active = False
            cart.save()

        return Response({"success": "Cart checked out successfully"}, status=200)
