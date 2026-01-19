from django.urls import path
from .views import user as user_views
from .views import organization as org_views

app_name = "iam"

urlpatterns = [
    path("users/", user_views.UserListView.as_view(), name="user_list"),
    path("users/add/", user_views.UserCreateView.as_view(), name="user_add"),
    path("users/<uuid:pk>/edit/", user_views.UserUpdateView.as_view(), name="user_edit"),
    path("users/<uuid:pk>/delete/", user_views.UserDeleteView.as_view(), name="user_delete"),
    
    # Organization URLs
    path("organization/", org_views.OrganizationDetailView.as_view(), name="organization_detail"),
    path("organization/edit/", org_views.OrganizationUpdateView.as_view(), name="organization_edit"),
]
