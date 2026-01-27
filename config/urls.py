from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Custom login view using admin/login.html template
    path('accounts/login/', auth_views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('apps.core.urls')),  # Root URL to Core Dashboard
    
    # Consolidated Apps
    path('housing/', include('apps.housing.urls')),  # Properties, Tenants, Leases
    path('finance/', include('apps.finance.urls')),  # Billing, Payments
    path('operations/', include('apps.operations.urls')),  # Maintenance, Documents, Notifications
    path('crm/', include('apps.crm.urls')), # Leads, Showings
    
    # Identity & Access Management
    path('iam/', include('apps.iam.urls')),
    
    # Removed administration app as it is merged into IAM
    # path('administration/', include('apps.administration.urls')),
    
    path('reporting/', include('apps.reporting.urls')),
    path('api/', include('config.api_urls')),
]
