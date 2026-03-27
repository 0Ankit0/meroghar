from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.finance.models import Expense, Invoice, Payment
from .serializers import ExpenseSerializer, InvoiceSerializer, PaymentSerializer
from apps.iam.api.permissions import IsOrgManager, IsOrgTenant
from apps.finance.services.khalti import KhaltiService

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [IsOrgManager]

    def get_queryset(self):
        active_org = getattr(self.request, 'active_organization', None)
        if active_org:
            return Expense.objects.filter(organization=active_org)
        return Expense.objects.none()

    def perform_create(self, serializer):
        serializer.save(organization=self.request.active_organization)

class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.none()
        active_org = getattr(self.request, 'active_organization', None)
        
        if active_org:
            queryset = Invoice.objects.filter(organization=active_org)
            
        # Tenant Restriction
        if user.role == 'TENANT':
            # Assuming Tenant profile is linked
            queryset = queryset.filter(lease__tenant__user=user)
            
        return queryset

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsOrgTenant]

    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.none()
        active_org = getattr(self.request, 'active_organization', None)
        
        if active_org:
            queryset = Payment.objects.filter(organization=active_org)
            
        # Tenant Restriction - View their own payments
        if user.role == 'TENANT':
            queryset = queryset.filter(invoice__lease__tenant__user=user)
            
        return queryset

    def perform_create(self, serializer):
        # Tenants might create payments? Usually initiated via mobile app.
        # We need validation to ensure they pay THEIR invoice.
        # Use serializer validation or check here.
        serializer.save(organization=self.request.active_organization)

    @action(detail=False, methods=['post'], url_path='initiate')
    def initiate(self, request):
        invoice_id = request.data.get('invoice_id')
        if not invoice_id:
            return Response({'detail': 'invoice_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            invoice = Invoice.objects.select_for_update().filter(
                id=invoice_id,
                organization=request.active_organization,
            ).first()
            if not invoice:
                return Response({'detail': 'Invoice not found.'}, status=status.HTTP_404_NOT_FOUND)

            payment = (
                Payment.objects.select_for_update()
                .filter(
                    invoice=invoice,
                    provider=Payment.Provider.KHALTI,
                    status=Payment.Status.INITIATED,
                    transaction_id='',
                )
                .order_by('-created_at')
                .first()
            )
            if not payment:
                payment = Payment.objects.create(
                    organization=invoice.organization,
                    invoice=invoice,
                    amount=invoice.total_amount - invoice.paid_amount,
                    status=Payment.Status.INITIATED,
                    provider=Payment.Provider.KHALTI,
                )

        khalti = KhaltiService()
        return_url = request.build_absolute_uri('/api/finance/payments/verify/')
        website_url = request.build_absolute_uri('/')
        data = khalti.initiate_payment(payment, return_url, website_url)
        if not data or 'payment_url' not in data:
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=['status', 'updated_at'])
            return Response({'detail': 'Failed to initiate Khalti payment.'}, status=status.HTTP_502_BAD_GATEWAY)

        payment.transaction_id = data.get('pidx', '')
        payment.provider_payload = data
        try:
            payment.save(update_fields=['transaction_id', 'provider_payload', 'updated_at'])
        except IntegrityError:
            existing_payment = Payment.objects.filter(
                provider=Payment.Provider.KHALTI,
                transaction_id=payment.transaction_id,
            ).exclude(pk=payment.pk).first()
            if not (existing_payment and existing_payment.invoice_id == payment.invoice_id):
                payment.status = Payment.Status.FAILED
                payment.save(update_fields=['status', 'updated_at'])
                return Response({'detail': 'Duplicate provider transaction detected.'}, status=status.HTTP_409_CONFLICT)

        return Response(
            {
                'payment_id': str(payment.id),
                'payment_url': data['payment_url'],
                'pidx': payment.transaction_id,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        pidx = request.data.get('pidx')
        if not pidx:
            return Response({'detail': 'pidx is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                payment = (
                    Payment.objects.select_for_update()
                    .select_related('invoice')
                    .get(provider=Payment.Provider.KHALTI, transaction_id=pidx)
                )
                invoice = payment.invoice
                if invoice:
                    invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)

                if payment.status == Payment.Status.SUCCESS:
                    return Response(
                        {
                            'detail': 'Payment already verified.',
                            'already_verified': True,
                            'payment_id': str(payment.id),
                        },
                        status=status.HTTP_200_OK,
                    )

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

                    return Response(
                        {
                            'detail': 'Payment verified.',
                            'already_verified': False,
                            'payment_id': str(payment.id),
                        },
                        status=status.HTTP_200_OK,
                    )

                payment.status = Payment.Status.FAILED
                payment.save(update_fields=['status', 'updated_at'])
                return Response({'detail': 'Payment verification failed.'}, status=status.HTTP_400_BAD_REQUEST)
        except Payment.DoesNotExist:
            return Response({'detail': 'Payment not found.'}, status=status.HTTP_404_NOT_FOUND)
