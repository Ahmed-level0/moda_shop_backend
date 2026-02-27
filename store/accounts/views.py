from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .serializers import ContactSerializer

from orders.models import Order


class ContactView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data['name']
            email = serializer.validated_data['email']
            subject = serializer.validated_data['subject']
            message = serializer.validated_data['message']

            full_message = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

            try:
                send_mail(
                    subject=f"Contact Form: {subject}",
                    message=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.DEFAULT_FROM_EMAIL],
                    fail_silently=False,
                )
                return Response({"message": "Email sent successfully"}, status=200)
            except Exception as e:
                return Response({"error": f"Failed to send email: {str(e)}"}, status=500)

        return Response(serializer.errors, status=400)


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
                "created": o.created_at,
                "address": o.address,
                "phonenumber": o.phone
            }
            for o in orders
        ]

        return Response({
            "username": user.username,
            "email": user.email,
            "orders": orders_data
        })
