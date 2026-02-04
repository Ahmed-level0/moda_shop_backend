from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from orders.models import Order


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        orders = Order.objects.filter(user=user)

        orders_data = [
            {
                "id": o.id,
                "status": o.status,
                "total": o.total_price,
                "created": o.created_at
            }
            for o in orders
        ]

        return Response({
            "username": user.username,
            "email": user.email,
            "orders": orders_data
        })
