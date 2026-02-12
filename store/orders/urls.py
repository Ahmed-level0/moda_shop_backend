from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UpdateOrderView

# Define URL patterns for product list and product detail views
urlpatterns = [
    path('update_order/', UpdateOrderView.as_view()),
]