from django.urls import path
from .views import PayOrderView, paymob_webhook

urlpatterns = [
    path("pay/<int:order_id>/", PayOrderView.as_view()),
    path("webhook/", paymob_webhook),
]