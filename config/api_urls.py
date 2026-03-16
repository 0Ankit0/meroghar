from django.urls import path, include
from rest_framework import routers

# Import ViewSets
from apps.iam.api.views import UserViewSet
from apps.crm.api.views import LeadViewSet, ShowingViewSet, RentalApplicationViewSet
from apps.operations.api.views import VendorViewSet, WorkOrderViewSet
from apps.housing.api.views import PropertyInspectionViewSet, InventoryItemViewSet, PropertyViewSet, UnitViewSet, TenantViewSet, LeaseViewSet
from apps.finance.api.views import ExpenseViewSet, InvoiceViewSet, PaymentViewSet

# Initialize DefaultRouter
router = routers.DefaultRouter()

# IAM
router.register(r'users', UserViewSet, basename='api-user')

# CRM
router.register(r'crm/leads', LeadViewSet, basename='api-lead')
router.register(r'crm/showings', ShowingViewSet, basename='api-showing')
router.register(r'crm/applications', RentalApplicationViewSet, basename='api-application')

# Operations
router.register(r'operations/vendors', VendorViewSet, basename='api-vendor')
router.register(r'operations/work-orders', WorkOrderViewSet, basename='api-workorder')

# Housing
router.register(r'housing/properties', PropertyViewSet, basename='api-property')
router.register(r'housing/units', UnitViewSet, basename='api-unit')
router.register(r'housing/tenants', TenantViewSet, basename='api-tenant')
router.register(r'housing/leases', LeaseViewSet, basename='api-lease')
router.register(r'housing/inspections', PropertyInspectionViewSet, basename='api-inspection')
router.register(r'housing/inventory', InventoryItemViewSet, basename='api-inventory')

# Finance
router.register(r'finance/expenses', ExpenseViewSet, basename='api-expense')
router.register(r'finance/invoices', InvoiceViewSet, basename='api-invoice')
router.register(r'finance/payments', PaymentViewSet, basename='api-payment')

from apps.reporting.api.views import MobileDashboardView
from django.urls import path

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/mobile/', MobileDashboardView.as_view(), name='api-mobile-dashboard'),
    path('iam/', include('apps.iam.api.urls')),
]
