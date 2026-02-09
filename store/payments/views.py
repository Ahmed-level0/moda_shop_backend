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

from django.db import transaction
from django.db.models import F
class PayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    # The method called when click on pay now
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

        # Check stock first
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order.id)
            for item in order.items.select_related("product").select_for_update():
                if item.product.stock < item.quantity:
                    return Response(
                        {"error": f"Not enough stock for {item.product.name} only {item.product.stock} left"},
                        status=409
                )
        
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

        paymob_order_id = order_response.get("id") # The id on Paymob site

        
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
                "integration_id": settings.PAYMOB_INTEGRATION_ID,
            }
        ).json()
        
        # "redirection_url": "http://127.0.0.1:8000/api/payments/callback/", # in case of development

        payment_token = payment_key_response.get("token") # The token used to generate the payment URL

        iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_token}"

        return Response({
            "payment_url": iframe_url
        })
    
@csrf_exempt
@api_view(["POST"])
def paymob_webhook(request):
    try:
        data = request.data
        obj = data.get("obj", {})
        print(data)
        print(obj)
        # Paymob sends the HMAC in the query params
        received_hmac = request.query_params.get("hmac")
        print(received_hmac)

        # 1. Extract the specific fields required for HMAC calculation
        # Order allows for flexibility but these are the standard fields for Paymob's HMAC
        hmac_fields = [
            "amount_cents",
            "created_at",
            "currency",
            "error_occured",
            "has_parent_transaction",
            "id",
            "integration_id",
            "is_3d_secure",
            "is_auth",
            "is_capture",
            "is_refunded",
            "is_standalone_payment",
            "is_voided",
            "order",
            "owner",
            "pending",
            "source_data.pan",
            "source_data.sub_type",
            "source_data.type",
            "success",
        ]

        concatenated_values = ""
        for field in hmac_fields:
            value = obj.get(field)
            if value is None:
                # Handle nested fields like source_data.pan
                if "." in field:
                    parent, child = field.split(".")
                    parent_obj = obj.get(parent, {})
                    value = parent_obj.get(child)
            
            # Convert boolean to string lower case 'true'/'false' as Paymob expects
            if isinstance(value, bool):
                value = str(value).lower()
            
            concatenated_values += str(value) if value is not None else ""

        # 2. Calculate HMAC
        calculated_hmac = hmac.new(
            settings.PAYMOB_HMAC_SECRET.encode(),
            concatenated_values.encode(),
            hashlib.sha512
        ).hexdigest()

        print(received_hmac)
        print(calculated_hmac)
        # 3. Secure Comparison
        if not hmac.compare_digest(received_hmac, calculated_hmac):
            return Response({"error": "Invalid HMAC"}, status=403)

        # 4. Process Payment
        if obj.get("success") is True:
            paymob_order_id = obj.get("order", {}).get("id")
            
            # Try to populate local order
            if paymob_order_id:
                try:
                    order = Order.objects.get(payment_reference=paymob_order_id)
                    order.status = "paid"
                    order.save()
                except Order.DoesNotExist:
                    # Log this error in production instead of returning info
                    return Response({"error": "Order not found"}, status=404)

        return Response({"status": "ok"})

    except Exception as e:
        # Avoid exploding on malformed data
        return Response({"error": "Webhook processing failed"}, status=400)


def check_paymob_payment(paymob_order_id):
    auth = requests.post(
        "https://accept.paymob.com/api/auth/tokens",
        json={"api_key": settings.PAYMOB_API_KEY}
    ).json()

    token = auth.get("token")

    response = requests.get(
        f"https://accept.paymob.com/api/ecommerce/orders/{paymob_order_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    ).json()

    if response.get("payment_status") == "PAID":
        return True
    return False

@api_view(["GET"])
def paymob_callback(request):
    try:
        # Paymob sends data in query params
        data = request.query_params.dict()
        
        # 1. Verify HMAC first (Avoiding API Call if possible)
        received_hmac = data.get("hmac")
        
        # Consistent HMAC fields for redirection (might differ slightly from Webhook, but usually same set)
        hmac_fields = [
            "amount_cents",
            "created_at",
            "currency",
            "error_occured",
            "has_parent_transaction",
            "id",
            "integration_id",
            "is_3d_secure",
            "is_auth",
            "is_capture",
            "is_refunded",
            "is_standalone_payment",
            "is_voided",
            "order",
            "owner",
            "pending",
            "source_data.pan",
            "source_data.sub_type",
            "source_data.type",
            "success",
        ]
        
        concatenated_values = ""
        for field in hmac_fields:
            value = data.get(field)
            # Boolean/None handling
            if value is None:
                value = "" # In query params, missing often means empty or not present
            else:
                # Paymob query params are strings, so "true" is "true".
                # But we need to ensure consistent formatting if needed.
                # Usually they come as strings already.
                pass 
                
            concatenated_values += str(value)

        calculated_hmac = hmac.new(
            settings.PAYMOB_HMAC_SECRET.encode(),
            concatenated_values.encode(),
            hashlib.sha512
        ).hexdigest()

        # If HMAC matches, we can trust the data
        if hmac.compare_digest(received_hmac, calculated_hmac):
             if data.get("success") == "true":
                paymob_order_id = data.get("order")
                try:
                    order = Order.objects.get(payment_reference=paymob_order_id)
                    if order.status != 'paid':
                        with transaction.atomic():
                            # Lock order row
                            order = Order.objects.select_for_update().get(id=order.id)
                            # Deduct stock
                            for item in order.items.all():
                                item.product.stock = F('stock') - item.quantity
                                item.product.save()

                            # Mark order paid
                            order.status = "paid"
                            order.save()
                    return Response({"message": "Payment Successful", "order_id": order.id})
                except Order.DoesNotExist:
                     return Response({"error": "Order not found"}, status=404)
        
        # Fallback: Check via API if HMAC fails or just to be sure
        paymob_order_id = data.get("order")
        if paymob_order_id and check_paymob_payment(paymob_order_id):
             try:
                order = Order.objects.get(payment_reference=paymob_order_id)
                if order.status != 'paid':
                    with transaction.atomic():
                        # Lock order row
                        order = Order.objects.select_for_update().get(id=order.id)
                        # Deduct stock
                        for item in order.items.all():
                            item.product.stock = F('stock') - item.quantity
                            item.product.save()

                        # Mark order paid
                        order.status = "paid"
                        order.save()
                return Response({"message": "Payment Successful", "order_id": order.id})
             except Order.DoesNotExist:
                 return Response({"error": "Order not found"}, status=404)

        return Response({"error": "Payment Failed or Invalid"}, status=400)

    except Exception as e:
        return Response({"error": str(e)}, status=400)
