from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PositionViewSet, TradeViewSet, DailyPnLViewSet, PortfolioSummaryView

router = DefaultRouter()
router.register(r"positions", PositionViewSet, basename="position")
router.register(r"trades",    TradeViewSet,    basename="trade")
router.register(r"dailypnl",  DailyPnLViewSet, basename="dailypnl")
router.register(r"",          PortfolioSummaryView, basename="portfolio")

urlpatterns = [path("", include(router.urls))]
