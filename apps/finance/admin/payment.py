from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone

from apps.finance.models import Payment, Invoice, Expense


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice', 'provider', 'amount', 'status', 'transaction_id', 'verified_at')
    list_filter = ('provider', 'status')
    search_fields = ('transaction_id', 'invoice__invoice_number')
    actions = ('mark_refunded', 'mark_chargeback_failed')

    @admin.action(description="Mark selected successful payments as refunded")
    def mark_refunded(self, request, queryset):
        updated = self._apply_reversal_status(queryset, Payment.Status.REFUNDED)
        self.message_user(request, f"Refunded {updated} payment(s).", level=messages.SUCCESS)

    @admin.action(description="Mark selected successful payments as chargeback/failed")
    def mark_chargeback_failed(self, request, queryset):
        updated = self._apply_reversal_status(queryset, Payment.Status.FAILED)
        self.message_user(request, f"Chargebacked {updated} payment(s).", level=messages.SUCCESS)

    def _apply_reversal_status(self, queryset, new_status):
        updated = 0
        for payment in queryset.select_related('invoice'):
            if payment.status != Payment.Status.SUCCESS:
                continue
            with transaction.atomic():
                locked_payment = Payment.objects.select_for_update().get(pk=payment.pk)
                invoice = locked_payment.invoice
                if invoice:
                    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
                    invoice.paid_amount = max(0, invoice.paid_amount - locked_payment.amount)
                    if invoice.paid_amount >= invoice.total_amount:
                        invoice.status = Invoice.Status.PAID
                    elif invoice.paid_amount > 0:
                        invoice.status = Invoice.Status.PARTIALLY_PAID
                    else:
                        invoice.status = Invoice.Status.OVERDUE if invoice.due_date < timezone.now().date() else Invoice.Status.SENT
                    invoice.save(update_fields=['paid_amount', 'status', 'updated_at'])

                locked_payment.status = new_status
                locked_payment.save(update_fields=['status', 'updated_at'])
                updated += 1
        return updated


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'organization', 'total_amount', 'paid_amount', 'status', 'due_date')
    list_filter = ('status',)
    search_fields = ('invoice_number',)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'property', 'amount', 'expense_date', 'category')
    list_filter = ('category',)
