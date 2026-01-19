from django.urls import path
from .views import reports

app_name = "reporting"

urlpatterns = [
    path("", reports.ReportListView.as_view(), name="report_list"),
    path("financial/", reports.FinancialReportView.as_view(), name="financial_report"),
    path("occupancy/", reports.OccupancyReportView.as_view(), name="occupancy_report"),
]
