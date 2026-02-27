from django.urls import path
from .views import MeView, ContactView

urlpatterns = [
    path("me/", MeView.as_view()),
    path("contact/", ContactView.as_view()),
]
