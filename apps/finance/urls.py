from django.urls import path
from .views import invoice as invoice_views
from .views import payment as payment_views
from .views import expense as expense_views

app_name = "finance"

urlpatterns = [
    # Invoices
    path("invoices/", invoice_views.InvoiceListView.as_view(), name="invoice_list"),
    path("invoices/add/", invoice_views.InvoiceCreateView.as_view(), name="invoice_add"),
    path("invoices/<uuid:pk>/", invoice_views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("invoices/<uuid:pk>/edit/", invoice_views.InvoiceUpdateView.as_view(), name="invoice_edit"),
    path("invoices/<uuid:pk>/delete/", invoice_views.InvoiceDeleteView.as_view(), name="invoice_delete"),
    
    # Payments
    path("payments/", payment_views.PaymentListView.as_view(), name="payment_list"),
    path("payments/initiate/<uuid:invoice_id>/", payment_views.InitiatePaymentView.as_view(), name="initiate_payment"),
    path("payments/verify/", payment_views.VerifyPaymentView.as_view(), name="verify_payment"),
    path("payments/<uuid:pk>/", payment_views.PaymentDetailView.as_view(), name="payment_detail"),
    path("payments/<uuid:pk>/edit/", payment_views.PaymentUpdateView.as_view(), name="payment_edit"),
    path("payments/<uuid:pk>/delete/", payment_views.PaymentDeleteView.as_view(), name="payment_delete"),

    # Expenses
    path('expenses/', expense_views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/add/', expense_views.ExpenseCreateView.as_view(), name='expense_add'),
    path('expenses/<uuid:pk>/', expense_views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('expenses/<uuid:pk>/edit/', expense_views.ExpenseUpdateView.as_view(), name='expense_edit'),
    path('expenses/<uuid:pk>/delete/', expense_views.ExpenseDeleteView.as_view(), name='expense_delete'),
]
