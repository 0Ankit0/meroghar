from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from ..models import Expense
from ..forms import ExpenseForm

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'finance/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.active_organization:
            return qs.filter(organization=self.request.active_organization)
        return qs.none()

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense_form.html'
    success_url = reverse_lazy('finance:expense_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.active_organization
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.active_organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'finance/expense_form.html'
    success_url = reverse_lazy('finance:expense_list')

    def get_form_kwargs(self):
         kwargs = super().get_form_kwargs()
         kwargs['organization'] = self.request.active_organization
         return kwargs

    def get_queryset(self):
        if self.request.active_organization:
             return Expense.objects.filter(organization=self.request.active_organization)
        return Expense.objects.none()

class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'finance/expense_detail.html'
    context_object_name = 'expense'

    def get_queryset(self):
        if self.request.active_organization:
             return Expense.objects.filter(organization=self.request.active_organization)
        return Expense.objects.none()

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'finance/expense_confirm_delete.html'
    success_url = reverse_lazy('finance:expense_list')

    def get_queryset(self):
        if self.request.active_organization:
             return Expense.objects.filter(organization=self.request.active_organization)
        return Expense.objects.none()
