from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModelRunViewSet, StrategyProfileViewSet

router = DefaultRouter()
router.register(r"strategies", StrategyProfileViewSet, basename="strategy")
router.register(r"runs", ModelRunViewSet, basename="modelrun")

urlpatterns = [path("", include(router.urls))]
