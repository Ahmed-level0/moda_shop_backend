from django.conf import settings
from django.urls import path, include
from .views import ProductListAPIView, ProductDetailAPIView
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# Define URL patterns for product list and product detail views
urlpatterns = [
    path('products/', ProductListAPIView.as_view()),
    path('products/<int:pk>/', ProductDetailAPIView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)