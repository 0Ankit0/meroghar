from django.urls import path
from .views import user as user_views
from .views import organization as org_views
from .views import group as group_views

app_name = "iam"

urlpatterns = [
    path("users/", user_views.UserListView.as_view(), name="user_list"),
    path("users/add/", user_views.UserCreateView.as_view(), name="user_add"),
    path("users/<uuid:pk>/edit/", user_views.UserUpdateView.as_view(), name="user_edit"),
    path("users/<uuid:pk>/delete/", user_views.UserDeleteView.as_view(), name="user_delete"),
    
    # Organization URLs
    path("organizations/", org_views.OrganizationListView.as_view(), name="organization_list"),
    path("organizations/add/", org_views.OrganizationCreateView.as_view(), name="organization_add"),
    path("organizations/switch/<uuid:pk>/", org_views.SwitchOrganizationView.as_view(), name="organization_switch"),
    path("organization/", org_views.OrganizationDetailView.as_view(), name="organization_detail"),
    path("organization/edit/", org_views.OrganizationUpdateView.as_view(), name="organization_edit"),
    
    # Organization Groups
    path("groups/", group_views.OrganizationGroupListView.as_view(), name="group_list"),
    path("groups/add/", group_views.OrganizationGroupCreateView.as_view(), name="group_add"),
    path("groups/<uuid:pk>/edit/", group_views.OrganizationGroupUpdateView.as_view(), name="group_edit"),
    path("groups/<uuid:pk>/delete/", group_views.OrganizationGroupDeleteView.as_view(), name="group_delete"),
]
