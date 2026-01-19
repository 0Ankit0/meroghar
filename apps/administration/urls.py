from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "administration"

router = DefaultRouter()
router.register(r'api/users', views.UserViewSet)

urlpatterns = [
    # Template Views
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/add/", views.UserCreateView.as_view(), name="user_add"),
    path("users/<uuid:pk>/edit/", views.UserUpdateView.as_view(), name="user_edit"),
    path("users/<uuid:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    
    # Auth
    path("auth/2fa/", views.TwoFactorVerificationView.as_view(), name="two_factor_verification"),
    
    # API Routes
    path('', include(router.urls)),
]
