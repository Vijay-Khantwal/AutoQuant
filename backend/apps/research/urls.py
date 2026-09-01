from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResearchRunViewSet, StockDecisionViewSet

router = DefaultRouter()
router.register(r"runs", ResearchRunViewSet, basename="researchrun")
router.register(r"decisions", StockDecisionViewSet, basename="stockdecision")

urlpatterns = [path("", include(router.urls))]
