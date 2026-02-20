from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from orders.models import Order, OrderItem

# Create your views here.

class UpdateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        order_id = request.data.get('id')
        phone = request.data.get('phone')
        address = request.data.get('address')
        items_data = request.data.get('items')

        if not order_id:
            return Response({"error": "Order ID is required"}, status=400)

        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status != 'pending':
            return Response({"error": "Only pending orders can be updated"}, status=400)

        if phone:
            order.phone = phone

        if address:
            order.address = address

        if items_data:

            for item_data in items_data:

                product_id = item_data.get('product_id')
                quantity = item_data.get('quantity')

                if product_id is None or quantity is None:
                    continue

                try:
                    order_item = OrderItem.objects.get(
                        order=order,
                        product_id=product_id
                    )

                    if int(quantity) <= 0:
                        order_item.delete()
                    else:
                        order_item.quantity = int(quantity)
                        order_item.save()

                except OrderItem.DoesNotExist:
                    continue

            # If no items left → delete order
            if not order.items.exists():
                order.delete()

                return Response({
                    "message": "Order deleted because it has no items"
                }, status=200)

            # Recalculate total
            items_total = sum(
                item.price * item.quantity
                for item in order.items.all()
            )

            # Recalculate discount if coupon exists
            if order.coupon:
                if order.coupon.discount_type == 'percentage':
                    order.discount_amount = items_total * order.coupon.discount / 100
                else:
                    order.discount_amount = min(order.coupon.discount, items_total)
            else:
                order.discount_amount = 0

            order.total_price = items_total - order.discount_amount

        order.save()

        return Response({
            "order_id": order.id,
            "message": "Order updated successfully",
            "total_price": order.total_price,
            "phone": order.phone,
            "address": order.address
        }, status=200)
