from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UpdateOrderView, OrderListView, OrderDetailView

# Define URL patterns for product list and product detail views
urlpatterns = [
    path('update_order/', UpdateOrderView.as_view()),
    path('user_orders/', OrderListView.as_view(), name='order-list'),
    path('order_details/<int:id>/', OrderDetailView.as_view(), name='order-detail'),
]