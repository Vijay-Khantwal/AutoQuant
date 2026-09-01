from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExecutionRunViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"runs", ExecutionRunViewSet, basename="executionrun")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [path("", include(router.urls))]
