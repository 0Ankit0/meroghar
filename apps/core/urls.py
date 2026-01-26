from django.urls import path
from .views import DashboardView
from .api.views import RevenueDataAPIView

app_name = "core"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("api/revenue-data/", RevenueDataAPIView.as_view(), name="revenue_data_api"),
]
