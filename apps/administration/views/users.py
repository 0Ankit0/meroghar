from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from apps.administration.serializers import UserSerializer

User = get_user_model()

# --- Access Control Mixin ---
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.role == 'ADMIN')

# --- Template Views ---

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = "administration/user_list.html"
    context_object_name = "users"
    ordering = ['-date_joined']

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'organization', 'password']
    template_name = "administration/user_form.html"
    success_url = reverse_lazy('administration:user_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'organization', 'is_active']
    template_name = "administration/user_form.html"
    success_url = reverse_lazy('administration:user_list')

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = "administration/user_confirm_delete.html"
    success_url = reverse_lazy('administration:user_list')

# --- API ViewSets ---

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
