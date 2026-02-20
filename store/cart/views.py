from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Cart, CartItem
from products.models import Product
from .serializers import CartSerializer
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from orders.models import Order, OrderItem
from coupons.models import Coupon

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
    def apply_coupon(self, request):
        code = request.data.get('code')
        if not code:
            return Response({"error": "Coupon code is required"}, status=400)
        
        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({"error": "Invalid coupon code"}, status=404)
        
        if not coupon.is_valid:
            return Response({"error": "Coupon is expired or invalid"}, status=400)
        
        cart = self.get_active_cart(request.user)
        cart.coupon = coupon
        cart.save()
        
        return Response(CartSerializer(cart).data, status=200)

    @action(detail=False, methods=['post'])
    def remove_coupon(self, request):
        cart = self.get_active_cart(request.user)
        cart.coupon = None
        cart.save()
        return Response(CartSerializer(cart).data, status=200)

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        cart = self.get_active_cart(request.user)

        if cart.items.count() == 0:
            return Response({"error": "Cart is empty"}, status=400)

        phone = request.data.get('phone')
        address = request.data.get('address')
        payment_method = request.data.get('payment_method', 'online')

        if not phone or not address:
            return Response({"error": "Phone and address required"}, status=400)

        # Calculate discount amount for storage
        discount_amount = 0
        if cart.coupon and cart.coupon.is_valid:
            items_total = sum(item.total_price for item in cart.items.all())
            if cart.coupon.discount_type == 'percentage':
                discount_amount = items_total * cart.coupon.discount / 100
            else:
                discount_amount = min(cart.coupon.discount, items_total)

        # Creating an order for the user
        order = Order.objects.create(
            user=request.user,
            total_price=cart.total_price,
            coupon=cart.coupon,
            discount_amount=discount_amount,
            phone=phone,
            address=address,
            status='pending' if payment_method == 'online' else 'cod'
        )

        # Creating and order item for each item in the cart
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity if item.quantity <= item.product.stock else item.product.stock, # for safety
                price=item.product.price
            )

        # If COD, deduct stock immediately
        if order.status == 'cod':
            from django.db import transaction
            from django.db.models import F
            with transaction.atomic():
                for item in order.items.all():
                    # Double check stock before final deduction
                    if item.product.stock < item.quantity:
                        return Response(
                            {"error": f"Not enough stock for {item.product.name} only {item.product.stock} left"},
                            status=409
                    )
                    item.product.stock = F('stock') - item.quantity
                    item.product.save()

        if cart.coupon:
            cart.coupon.usage_count = models.F('usage_count') + 1
            cart.coupon.save()

        cart.is_active = False
        cart.save()
        
        # Create a new active cart for the user
        Cart.objects.create(user=request.user)
        
        message = "Order created. Payment required." if order.status == 'pending' else "Order placed successfully (Cash on Delivery)."
        
        return Response({
            "order_id": order.id,
            "message": message,
            "status": order.status
        }, status=201)