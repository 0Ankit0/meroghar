from django.urls import path
from .views import work_order as wo_views
from .views import document as doc_views
from .views import notification as notif_views
from .views import vendor as vendor_views

app_name = "operations"

urlpatterns = [
    # Work Orders
    path("maintenance/", wo_views.WorkOrderListView.as_view(), name="work_order_list"),
    path("maintenance/add/", wo_views.WorkOrderCreateView.as_view(), name="work_order_add"),
    path("maintenance/<uuid:pk>/", wo_views.WorkOrderDetailView.as_view(), name="work_order_detail"),
    path("maintenance/<uuid:pk>/edit/", wo_views.WorkOrderUpdateView.as_view(), name="work_order_edit"),
    path("maintenance/<uuid:pk>/delete/", wo_views.WorkOrderDeleteView.as_view(), name="work_order_delete"),
    
    # Documents
    path("documents/", doc_views.DocumentListView.as_view(), name="document_list"),
    path("documents/add/", doc_views.DocumentCreateView.as_view(), name="document_add"),
    path("documents/<uuid:pk>/", doc_views.DocumentDetailView.as_view(), name="document_detail"),
    path("documents/<uuid:pk>/delete/", doc_views.DocumentDeleteView.as_view(), name="document_delete"),
    
    # Vendors
    path('vendors/', vendor_views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/add/', vendor_views.VendorCreateView.as_view(), name='vendor_add'),
    path('vendors/<uuid:pk>/edit/', vendor_views.VendorUpdateView.as_view(), name='vendor_edit'),
    
    # Notifications
    path("notifications/", notif_views.NotificationListView.as_view(), name="notification_list"),
    path("notifications/<uuid:pk>/", notif_views.NotificationDetailView.as_view(), name="notification_detail"),
    path("notifications/<uuid:pk>/delete/", notif_views.NotificationDeleteView.as_view(), name="notification_delete"),
]
