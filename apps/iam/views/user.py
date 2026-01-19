from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from apps.iam.models import User

# User = get_user_model() # Good practice to use this

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.role == 'ADMIN')

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = "iam/user_list.html"
    context_object_name = "users"
    
    def get_queryset(self):
        # Admin sees all, Managers might see only their org users?
        # For now, admin only
        return User.objects.all().order_by('-date_joined')

class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'organization', 'password'] # Password handling needs care
    template_name = "iam/user_form.html"
    success_url = reverse_lazy('iam:user_list')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        return super().form_valid(form)

class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name', 'role', 'organization', 'is_active']
    template_name = "iam/user_form.html"
    success_url = reverse_lazy('iam:user_list')
    # Prevent password update here for simplicity, force password reset flow or separate view

class UserDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = User
    template_name = "iam/user_confirm_delete.html"
    success_url = reverse_lazy('iam:user_list')
