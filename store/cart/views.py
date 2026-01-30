from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from orders.models import Order, OrderItem

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
            return Response({"error": "Cart is empty"}, status=400)

        phone = request.data.get('phone')
        address = request.data.get('address')

        if not phone or not address:
            return Response({"error": "Phone and address required"}, status=400)

        order = Order.objects.create(
            user=request.user,
            total_price=cart.total_price,
            phone=phone,
            address=address,
            status='pending'
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        cart.is_active = False
        cart.save()
        
        # Create a new active cart for the user
        Cart.objects.create(user=request.user)
        return Response({
            "order_id": order.id,
            "message": "Order created. Payment required."
        }, status=201)
    

"""
# Confirm Payment API View (Simulation)

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from .models import Order
from cart.models import Cart

class ConfirmPaymentAPIView(APIView):
    def post(self, request):
        order_id = request.data.get('order_id')
        payment_reference = request.data.get('payment_reference')

        order = Order.objects.get(id=order_id)

        if order.payment_status == 'paid':
            return Response({"detail": "Order already paid"})

        with transaction.atomic():
            for item in order.items.all():
                if item.quantity > item.product.stock:
                    order.payment_status = 'failed'
                    order.save()
                    return Response({"error": "Not enough stock"}, status=400)

                item.product.stock -= item.quantity
                item.product.save()

            order.payment_status = 'paid'
            order.payment_reference = payment_reference
            order.save()

            Cart.objects.filter(user=order.user, is_active=True).update(is_active=False)

        return Response({"success": "Payment confirmed"})
    """