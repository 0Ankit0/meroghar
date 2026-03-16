from django.urls import path

from apps.iam.api import views

urlpatterns = [
    path('auth/login/', views.AuthLoginApiView.as_view(), name='api-iam-login'),
    path('auth/refresh/', views.AuthRefreshTokenApiView.as_view(), name='api-iam-refresh'),
    path('auth/logout/', views.AuthLogoutApiView.as_view(), name='api-iam-logout'),
    path('auth/profile/', views.AuthProfileApiView.as_view(), name='api-iam-profile'),
    path('memberships/', views.MembershipListApiView.as_view(), name='api-iam-memberships'),
    path('switch-organization/', views.SwitchOrganizationApiView.as_view(), name='api-iam-switch-organization'),
]
