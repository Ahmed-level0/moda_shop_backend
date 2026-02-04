import requests
import hmac
import hashlib
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from orders.models import Order

class PayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        if order.status != "pending":
            return Response({"error": "Order already processed"}, status=400)

        # Get Auth Token
        auth_response = requests.post(
            "https://accept.paymob.com/api/auth/tokens",
            json={"api_key": settings.PAYMOB_API_KEY}
        ).json()

        token = auth_response.get("token")

        if not token:
            return Response({"error": "Paymob auth failed"}, status=500)

        # Create Paymob Order
        order_response = requests.post(
            "https://accept.paymob.com/api/ecommerce/orders",
            json={
                "auth_token": token,
                "delivery_needed": "false",
                "amount_cents": int(order.total_price * 100),
                "currency": "EGP",
                "items": []
            }
        ).json()

        paymob_order_id = order_response.get("id")
        
        order.payment_reference = paymob_order_id
        order.save()

        # Payment Key
        payment_key_response = requests.post(
            "https://accept.paymob.com/api/acceptance/payment_keys",
            json={
                "auth_token": token,
                "amount_cents": int(order.total_price * 100),
                "expiration": 3600,
                "order_id": paymob_order_id,
                "billing_data": {
                    "apartment": "NA",
                    "email": request.user.email,
                    "floor": "NA",
                    "first_name": request.user.username,
                    "street": order.address,
                    "building": "NA",
                    "phone_number": order.phone,
                    "shipping_method": "NA",
                    "postal_code": "NA",
                    "city": "Cairo",
                    "country": "EG",
                    "last_name": request.user.username,
                    "state": "Cairo"
                },
                "currency": "EGP",
                "integration_id": settings.PAYMOB_INTEGRATION_ID
            }
        ).json()

        payment_token = payment_key_response.get("token")

        iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_token}"

        return Response({
            "payment_url": iframe_url
        })


@csrf_exempt
@api_view(["POST"])
def paymob_webhook(request):
    payload = request.body
    received_hmac = request.GET.get("hmac")
    calculated_hmac = hmac.new(
        settings.PAYMOB_HMAC_SECRET.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()

    if received_hmac != calculated_hmac:
        return Response({"error": "Invalid HMAC"}, status=403)

    data = json.loads(payload)

    if data.get("obj", {}).get("success") is True:
        paymob_order_id = data["obj"]["order"]["id"]

        try:
            order = Order.objects.get(payment_reference=paymob_order_id)
            order.status = "paid"
            order.save()
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

    return Response({"status": "ok"})
