from .document import DocumentCreateView, DocumentDeleteView, DocumentDetailView, DocumentListView
from .notification import NotificationDeleteView, NotificationDetailView, NotificationListView
from .vendor import VendorCreateView, VendorListView, VendorUpdateView
from .work_order import (
    WorkOrderCreateView,
    WorkOrderDeleteView,
    WorkOrderDetailView,
    WorkOrderListView,
    WorkOrderUpdateView,
)

__all__ = [
    "WorkOrderListView",
    "WorkOrderCreateView",
    "WorkOrderDetailView",
    "WorkOrderUpdateView",
    "WorkOrderDeleteView",
    "DocumentListView",
    "DocumentCreateView",
    "DocumentDetailView",
    "DocumentDeleteView",
    "NotificationListView",
    "NotificationDetailView",
    "NotificationDeleteView",
    "VendorListView",
    "VendorCreateView",
    "VendorUpdateView",
]
