from django.urls import path
from .views import property as property_views
from .views import tenant as tenant_views
from .views import lease as lease_views

app_name = "housing"

urlpatterns = [
    # Properties
    path("properties/", property_views.PropertyListView.as_view(), name="property_list"),
    path("properties/add/", property_views.PropertyCreateView.as_view(), name="property_add"),
    path("properties/<uuid:pk>/", property_views.PropertyDetailView.as_view(), name="property_detail"),
    path("properties/<uuid:pk>/edit/", property_views.PropertyUpdateView.as_view(), name="property_edit"),
    path("properties/<uuid:pk>/delete/", property_views.PropertyDeleteView.as_view(), name="property_delete"),
    
    # Tenants
    path("tenants/", tenant_views.TenantListView.as_view(), name="tenant_list"),
    path("tenants/add/", tenant_views.TenantCreateView.as_view(), name="tenant_add"),
    path("tenants/<uuid:pk>/", tenant_views.TenantDetailView.as_view(), name="tenant_detail"),
    path("tenants/<uuid:pk>/edit/", tenant_views.TenantUpdateView.as_view(), name="tenant_edit"),
    path("tenants/<uuid:pk>/delete/", tenant_views.TenantDeleteView.as_view(), name="tenant_delete"),
    
    # Leases
    path("leases/", lease_views.LeaseListView.as_view(), name="lease_list"),
    path("leases/add/", lease_views.LeaseCreateView.as_view(), name="lease_add"),
    path("leases/<uuid:pk>/", lease_views.LeaseDetailView.as_view(), name="lease_detail"),
    path("leases/<uuid:pk>/edit/", lease_views.LeaseUpdateView.as_view(), name="lease_edit"),
    path("leases/<uuid:pk>/delete/", lease_views.LeaseDeleteView.as_view(), name="lease_delete"),
]
