from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("api/signals/",   include("apps.signals.urls")),
    path("api/research/",  include("apps.research.urls")),
    path("api/execution/", include("apps.execution.urls")),
    path("api/portfolio/", include("apps.portfolio.urls")),
    path("api/model/",     include("apps.model_mgmt.urls")),
]
