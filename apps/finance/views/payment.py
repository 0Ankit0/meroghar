from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.db import IntegrityError, transaction
from ..models import Payment, Invoice
from ..services.khalti import KhaltiService

class InitiatePaymentView(LoginRequiredMixin, View):
    def post(self, request, invoice_id):
        if not request.active_organization:
            messages.error(request, "No active organization selected.")
            return redirect('finance:invoice_list')

        invoice = get_object_or_404(
            Invoice.objects.filter(organization=request.active_organization),
            id=invoice_id,
        )
        
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
            payment.transaction_id = data.get('pidx', '')
            payment.provider_payload = data
            try:
                payment.save(update_fields=['transaction_id', 'provider_payload', 'updated_at'])
            except IntegrityError:
                existing_payment = Payment.objects.filter(
                    provider=Payment.Provider.KHALTI,
                    transaction_id=payment.transaction_id,
                ).exclude(pk=payment.pk).first()
                if existing_payment and existing_payment.invoice_id == payment.invoice_id:
                    return redirect(data['payment_url'])
                payment.status = Payment.Status.FAILED
                payment.save(update_fields=['status', 'updated_at'])
                messages.error(request, "Duplicate provider transaction detected.")
                return redirect('finance:invoice_detail', pk=invoice.id)
            
            return redirect(data['payment_url'])
        else:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=['status', 'updated_at'])
            messages.error(request, "Failed to initiate Khalti payment.")
            return redirect('finance:invoice_detail', pk=invoice.id)

class VerifyPaymentView(LoginRequiredMixin, View):
    def get(self, request):
        pidx = request.GET.get('pidx')
        if not pidx:
             messages.error(request, "Invalid verification request.")
             return redirect('dashboard')

        try:
            with transaction.atomic():
                # Find payment with lock
                try:
                     payment_qs = Payment.objects.select_for_update()
                     if request.active_organization:
                         payment_qs = payment_qs.filter(organization=request.active_organization)
                     payment = payment_qs.get(transaction_id=pidx)
                except Payment.DoesNotExist:
                     # If not found by transaction_id, try by purchase_order_id (ID) if valid
                     # But Khalti doc says pidx is key.
                     messages.error(request, "Payment record not found.")
                     return redirect('finance:invoice_list')

                invoice = payment.invoice

                if payment.status == Payment.Status.SUCCESS:
                    messages.info(request, "Payment already verified.")
                    if invoice:
                        return redirect('finance:invoice_detail', pk=invoice.id)
                    return redirect('finance:invoice_list')

                khalti = KhaltiService()
                verification_data = khalti.verify_payment(pidx)
                
                if verification_data and verification_data.get('status') == 'Completed':
                    payment.status = Payment.Status.SUCCESS
                    payment.verified_at = timezone.now()
                    payment.provider_payload = verification_data
                    payment.save(update_fields=['status', 'verified_at', 'provider_payload', 'updated_at'])

                    if invoice:
                        invoice.paid_amount += payment.amount
                        if invoice.paid_amount >= invoice.total_amount:
                            invoice.status = Invoice.Status.PAID
                        else:
                            invoice.status = Invoice.Status.PARTIALLY_PAID
                        invoice.save(update_fields=['paid_amount', 'status', 'updated_at'])
                    
                    messages.success(request, f"Payment successful! Invoice {invoice.invoice_number if invoice else ''} updated.")
                    if invoice:
                        return redirect('finance:invoice_detail', pk=invoice.id)
                    return redirect('finance:invoice_list')
                
                else:
                    payment.status = Payment.Status.FAILED
                    payment.save(update_fields=['status', 'updated_at'])
                    messages.error(request, "Payment verification failed or not completed.")
                    if invoice:
                        return redirect('finance:invoice_detail', pk=invoice.id)
                    return redirect('finance:invoice_list')

        except Payment.DoesNotExist:
            messages.error(request, "Payment record not found.")
            return redirect('finance:invoice_list')
        except Exception as e:
            messages.error(request, f"System error during verification: {e}")
            return redirect('finance:invoice_list')

class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.active_organization:
             qs = qs.filter(organization=self.request.active_organization)
        else:
             qs = qs.none()
        return qs

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'finance/payment_detail.html'
    context_object_name = 'payment'
    
    def get_queryset(self):
        if self.request.active_organization:
            return Payment.objects.filter(organization=self.request.active_organization)
        return Payment.objects.none()

class PaymentUpdateView(LoginRequiredMixin, UpdateView):
    model = Payment
    fields = ['invoice', 'amount', 'payment_method', 'status', 'notes']
    template_name = 'finance/payment_form.html'
    success_url = reverse_lazy('finance:payment_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Payment.objects.filter(organization=self.request.active_organization)
        return Payment.objects.none()

class PaymentDeleteView(LoginRequiredMixin, DeleteView):
    model = Payment
    template_name = 'finance/payment_confirm_delete.html'
    success_url = reverse_lazy('finance:payment_list')
    
    def get_queryset(self):
        if self.request.active_organization:
            return Payment.objects.filter(organization=self.request.active_organization)
        return Payment.objects.none()
