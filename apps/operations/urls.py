from django.urls import path
from .views import work_order as work_order_views
from .views import document as document_views
from .views import notification as notification_views

app_name = "operations"

urlpatterns = [
    # Work Orders
    path("maintenance/", work_order_views.WorkOrderListView.as_view(), name="work_order_list"),
    path("maintenance/add/", work_order_views.WorkOrderCreateView.as_view(), name="work_order_add"),
    path("maintenance/<uuid:pk>/", work_order_views.WorkOrderDetailView.as_view(), name="work_order_detail"),
    path("maintenance/<uuid:pk>/edit/", work_order_views.WorkOrderUpdateView.as_view(), name="work_order_edit"),
    path("maintenance/<uuid:pk>/delete/", work_order_views.WorkOrderDeleteView.as_view(), name="work_order_delete"),
    
    # Documents
    path("documents/", document_views.DocumentListView.as_view(), name="document_list"),
    path("documents/add/", document_views.DocumentCreateView.as_view(), name="document_add"),
    path("documents/<uuid:pk>/", document_views.DocumentDetailView.as_view(), name="document_detail"),
    path("documents/<uuid:pk>/delete/", document_views.DocumentDeleteView.as_view(), name="document_delete"),
    
    # Notifications
    path("notifications/", notification_views.NotificationListView.as_view(), name="notification_list"),
    path("notifications/<uuid:pk>/", notification_views.NotificationDetailView.as_view(), name="notification_detail"),
    path("notifications/<uuid:pk>/delete/", notification_views.NotificationDeleteView.as_view(), name="notification_delete"),
]
