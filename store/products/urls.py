from django.urls import path, include
from .views import ProductListAPIView, ProductDetailAPIView
from rest_framework.routers import DefaultRouter

# Define URL patterns for product list and product detail views
urlpatterns = [
    path('products/', ProductListAPIView.as_view()),
    path('products/<int:pk>/', ProductDetailAPIView.as_view()),
]