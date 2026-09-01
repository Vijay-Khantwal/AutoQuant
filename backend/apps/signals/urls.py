from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignalRunViewSet

router = DefaultRouter()
router.register(r"runs", SignalRunViewSet, basename="signalrun")

urlpatterns = [path("", include(router.urls))]
