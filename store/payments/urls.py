from django.urls import path
from .views import PayOrderView, paymob_webhook, paymob_callback

urlpatterns = [
    path("pay/<int:order_id>/", PayOrderView.as_view()),
    path("webhook/", paymob_webhook),
    path("callback/", paymob_callback, name="paymob_callback"),
]