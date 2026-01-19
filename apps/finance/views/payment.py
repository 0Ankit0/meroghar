from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from ..models import Payment, Invoice
from ..services.khalti import KhaltiService

class InitiatePaymentView(LoginRequiredMixin, View):
    def post(self, request, invoice_id):
        invoice = get_object_or_404(Invoice, id=invoice_id)
        
        # Create a payment record
        payment = Payment.objects.create(
            organization=invoice.organization,
            invoice=invoice,
            amount=invoice.total_amount - invoice.paid_amount, # Paying remaining balance
            status=Payment.Status.INITIATED,
            provider=Payment.Provider.KHALTI
        )
        
        # Build URLs
        return_url = request.build_absolute_uri(reverse('finance:verify_payment'))
        website_url = request.build_absolute_uri('/')
        
        # Call Service
        khalti = KhaltiService()
        data = khalti.initiate_payment(payment, return_url, website_url)
        
        if data and 'payment_url' in data:
            # Update payment with pidx
            payment.transaction_id = data.get('pidx')
            payment.provider_payload = data
            payment.save()
            
            return redirect(data['payment_url'])
        else:
            payment.status = Payment.Status.FAILED
            payment.save()
            messages.error(request, "Failed to initiate Khalti payment.")
            return redirect('finance:invoice_detail', pk=invoice.id)

class VerifyPaymentView(LoginRequiredMixin, View):
    def get(self, request):
        # Khalti redirects back with ?pidx=...&status=...&purchase_order_id=...
        pidx = request.GET.get('pidx')
        status = request.GET.get('status')
        purchase_order_id = request.GET.get('purchase_order_id') # Payment ID
        
        if not pidx:
             messages.error(request, "Invalid verification request.")
             return redirect('dashboard')
             
        # Find payment
        try:
             payment = Payment.objects.get(transaction_id=pidx)
        except Payment.DoesNotExist:
             messages.error(request, "Payment record not found.")
             return redirect('finance:invoice_list')

        # Call verify on Khalti
        khalti = KhaltiService()
        verification_data = khalti.verify_payment(pidx)
        
        if verification_data and verification_data.get('status') == 'Completed':
            # Mark payment success
            payment.status = Payment.Status.SUCCESS
            payment.verified_at = timezone.now()
            payment.provider_payload = verification_data # Store final data
            payment.save()
            
            # Update Invoice
            invoice = payment.invoice
            if invoice:
                # Update paid amount
                invoice.paid_amount += payment.amount
                
                # Update status
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = Invoice.Status.PAID
                else:
                    invoice.status = Invoice.Status.PARTIALLY_PAID
                invoice.save()
            
            messages.success(request, f"Payment successful! Invoice {invoice.invoice_number} updated.")
            return redirect('finance:invoice_detail', pk=invoice.id)
        
        else:
             payment.status = Payment.Status.FAILED
             payment.save()
             messages.error(request, "Payment verification failed or not completed.")
             if payment.invoice:
                 return redirect('finance:invoice_detail', pk=payment.invoice.id)
             return redirect('finance:invoice_list')

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request.user, 'organization') and self.request.user.organization:
             qs = qs.filter(organization=self.request.user.organization)
        return qs

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'finance/payment_detail.html'
    context_object_name = 'payment'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Payment.objects.filter(organization=user.organization)
        return Payment.objects.none()

class PaymentUpdateView(LoginRequiredMixin, UpdateView):
    model = Payment
    fields = ['invoice', 'amount', 'payment_method', 'status', 'notes']
    template_name = 'finance/payment_form.html'
    success_url = reverse_lazy('finance:payment_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Payment.objects.filter(organization=user.organization)
        return Payment.objects.none()

class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = Payment
    template_name = 'finance/payment_confirm_delete.html'
    success_url = reverse_lazy('finance:payment_list')
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.organization:
            return Payment.objects.filter(organization=user.organization)
        return Payment.objects.none()
