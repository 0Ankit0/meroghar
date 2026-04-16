'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { analytics } from '@/lib/analytics';
import { PaymentEvents } from '@/lib/analytics/events';
import {
  buildInvoiceApiParams,
  normalizeAdditionalCharge,
  normalizeInvoice,
  normalizeInvoiceListResponse,
  normalizeRentLedger,
  normalizeUtilityBill,
  normalizeUtilityBillAttachment,
  normalizeUtilityBillDispute,
  normalizeUtilityBillHistory,
  normalizeUtilityBillListResponse,
  normalizeUtilityBillShareListResponse,
} from '@/lib/finances';
import type {
  AdditionalChargeCreatePayload,
  AdditionalChargeDisputePayload,
  AdditionalChargeResolvePayload,
  InitiatePaymentRequest,
  InitiatePaymentResponse,
  InvoiceListParams,
  InvoiceListResponse,
  InvoicePaymentPayload,
  InvoiceRecord,
  PaymentProvider,
  PaymentTransaction,
  RentLedger,
  UtilityBillAttachment,
  UtilityBillAttachmentUploadPayload,
  UtilityBillCreatePayload,
  UtilityBillDispute,
  UtilityBillDisputePayload,
  UtilityBillDisputeResolvePayload,
  UtilityBillHistory,
  UtilityBillListResponse,
  UtilityBillRecord,
  UtilityBillShareListResponse,
  UtilityBillSplitConfigurePayload,
  VerifyPaymentRequest,
  VerifyPaymentResponse,
} from '@/types';

function invalidateBillingQueries(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['billing'] });
  queryClient.invalidateQueries({ queryKey: ['transactions'] });
}

function parseFilename(headerValue?: string): string {
  if (!headerValue) {
    return 'receipt.txt';
  }

  const match = /filename="?([^"]+)"?/i.exec(headerValue);
  return match?.[1] ?? 'receipt.txt';
}

export function usePaymentProviders() {
  return useQuery({
    queryKey: ['payment-providers'],
    queryFn: async () => {
      const response = await apiClient.get<PaymentProvider[]>('/payments/providers/');
      return response.data;
    },
  });
}

export function useInitiatePayment() {
  return useMutation({
    mutationFn: async (data: InitiatePaymentRequest) => {
      const response = await apiClient.post<InitiatePaymentResponse>('/payments/initiate/', data);
      return response.data;
    },
    onSuccess: (_data, variables) => {
      analytics.capture(PaymentEvents.PAYMENT_INITIATED, {
        provider: variables.provider,
        amount: variables.amount,
        order_id: variables.purchase_order_id,
      });
    },
  });
}

export function useVerifyPayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: VerifyPaymentRequest) => {
      const response = await apiClient.post<VerifyPaymentResponse>('/payments/verify/', data);
      return response.data;
    },
    onSuccess: (data) => {
      invalidateBillingQueries(queryClient);
      analytics.capture(
        data.status === 'completed' ? PaymentEvents.PAYMENT_COMPLETED : PaymentEvents.PAYMENT_FAILED,
        { provider: data.provider, status: data.status },
      );
    },
  });
}

export function useTransaction(transactionId: string) {
  return useQuery({
    queryKey: ['transactions', transactionId],
    queryFn: async () => {
      const response = await apiClient.get<PaymentTransaction>(`/payments/${transactionId}/`);
      return response.data;
    },
    enabled: Boolean(transactionId),
  });
}

/** Backend returns list (not paginated). Uses offset/limit params. */
export function useTransactions(params?: { limit?: number; offset?: number; provider?: string }) {
  return useQuery({
    queryKey: ['transactions', params],
    queryFn: async () => {
      const response = await apiClient.get<PaymentTransaction[]>('/payments/', { params });
      return response.data;
    },
  });
}

export function useInvoices(params?: InvoiceListParams) {
  return useQuery<InvoiceListResponse>({
    queryKey: ['billing', 'invoices', params],
    queryFn: async () => {
      const response = await apiClient.get<unknown>('/invoices', {
        params: buildInvoiceApiParams(params),
      });
      return normalizeInvoiceListResponse(response.data);
    },
  });
}

export function useInvoice(invoiceId: string) {
  return useQuery<InvoiceRecord>({
    queryKey: ['billing', 'invoice', invoiceId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/invoices/${invoiceId}`);
      return normalizeInvoice(response.data);
    },
    enabled: Boolean(invoiceId),
  });
}

export function usePayInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ invoiceId, data }: { invoiceId: string; data: InvoicePaymentPayload }) => {
      const response = await apiClient.post<InitiatePaymentResponse>(`/invoices/${invoiceId}/pay`, data);
      return response.data;
    },
    onSuccess: (_response, variables) => {
      invalidateBillingQueries(queryClient);
      analytics.capture(PaymentEvents.PAYMENT_INITIATED, {
        provider: variables.data.provider,
        amount: variables.data.amount,
        order_id: `invoice-${variables.invoiceId}`,
      });
    },
  });
}

export function usePartialPayInvoice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ invoiceId, data }: { invoiceId: string; data: InvoicePaymentPayload }) => {
      const response = await apiClient.post<InitiatePaymentResponse>(
        `/invoices/${invoiceId}/partial-pay`,
        data,
      );
      return response.data;
    },
    onSuccess: (_response, variables) => {
      invalidateBillingQueries(queryClient);
      analytics.capture(PaymentEvents.PAYMENT_INITIATED, {
        provider: variables.data.provider,
        amount: variables.data.amount,
        order_id: `invoice-partial-${variables.invoiceId}`,
      });
    },
  });
}

export function useDownloadInvoiceReceipt() {
  return useMutation({
    mutationFn: async (invoiceId: string) => {
      const response = await apiClient.get<string>(`/invoices/${invoiceId}/receipt`, {
        responseType: 'text',
      });

      return {
        content: response.data,
        filename: parseFilename(response.headers['content-disposition']),
      };
    },
  });
}

export function useRentLedger(bookingId: string) {
  return useQuery<RentLedger>({
    queryKey: ['billing', 'rent-ledger', bookingId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/bookings/${bookingId}/rent-ledger`);
      return normalizeRentLedger(response.data);
    },
    enabled: Boolean(bookingId),
  });
}

export function useCreateAdditionalCharge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ bookingId, data }: { bookingId: string; data: AdditionalChargeCreatePayload }) => {
      const response = await apiClient.post<unknown>(`/bookings/${bookingId}/additional-charges`, data);
      return normalizeAdditionalCharge(response.data);
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function useDisputeAdditionalCharge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ chargeId, data }: { chargeId: string; data: AdditionalChargeDisputePayload }) => {
      const response = await apiClient.post<unknown>(`/additional-charges/${chargeId}/dispute`, data);
      return normalizeAdditionalCharge(response.data);
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function useResolveAdditionalCharge() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ chargeId, data }: { chargeId: string; data: AdditionalChargeResolvePayload }) => {
      const response = await apiClient.post<unknown>(`/additional-charges/${chargeId}/resolve`, data);
      return normalizeAdditionalCharge(response.data);
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function usePropertyUtilityBills(propertyId: string, params?: { page?: number; per_page?: number }) {
  return useQuery<UtilityBillListResponse>({
    queryKey: ['billing', 'utility-bills', propertyId, params],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/properties/${propertyId}/utility-bills`, {
        params,
      });
      return normalizeUtilityBillListResponse(response.data);
    },
    enabled: Boolean(propertyId),
  });
}

export function useCreateUtilityBill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ propertyId, data }: { propertyId: string; data: UtilityBillCreatePayload }) => {
      const response = await apiClient.post<unknown>(`/properties/${propertyId}/utility-bills`, data);
      return normalizeUtilityBill(response.data);
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function useUploadUtilityBillAttachment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      billId,
      data,
    }: {
      billId: string;
      data: UtilityBillAttachmentUploadPayload;
    }) => {
      const formData = new FormData();
      formData.append('file', data.file);
      const response = await apiClient.post<unknown>(`/utility-bills/${billId}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return normalizeUtilityBillAttachment(response.data) as UtilityBillAttachment;
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function useConfigureUtilityBillSplits() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ billId, data }: { billId: string; data: UtilityBillSplitConfigurePayload }) => {
      const response = await apiClient.post<unknown>(`/utility-bills/${billId}/splits`, data);
      return normalizeUtilityBill(response.data) as UtilityBillRecord;
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function usePublishUtilityBill() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (billId: string) => {
      const response = await apiClient.post<unknown>(`/utility-bills/${billId}/publish`);
      return normalizeUtilityBill(response.data) as UtilityBillRecord;
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function useTenantBillShares() {
  return useQuery<UtilityBillShareListResponse>({
    queryKey: ['billing', 'bill-shares'],
    queryFn: async () => {
      const response = await apiClient.get<unknown>('/tenants/me/bill-shares');
      return normalizeUtilityBillShareListResponse(response.data);
    },
  });
}

export function usePayBillShare() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ billShareId, data }: { billShareId: string; data: InvoicePaymentPayload }) => {
      const response = await apiClient.post<InitiatePaymentResponse>(`/bill-shares/${billShareId}/pay`, data);
      return response.data;
    },
    onSuccess: (_response, variables) => {
      invalidateBillingQueries(queryClient);
      analytics.capture(PaymentEvents.PAYMENT_INITIATED, {
        provider: variables.data.provider,
        amount: variables.data.amount,
        order_id: `bill-share-${variables.billShareId}`,
      });
    },
  });
}

export function useDisputeBillShare() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ billShareId, data }: { billShareId: string; data: UtilityBillDisputePayload }) => {
      const response = await apiClient.post<unknown>(`/bill-shares/${billShareId}/dispute`, data);
      return normalizeUtilityBillDispute(response.data) as UtilityBillDispute;
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function useResolveBillShareDispute() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      billShareId,
      data,
    }: {
      billShareId: string;
      data: UtilityBillDisputeResolvePayload;
    }) => {
      const response = await apiClient.post<unknown>(`/bill-shares/${billShareId}/resolve-dispute`, data);
      return normalizeUtilityBillDispute(response.data) as UtilityBillDispute;
    },
    onSuccess: () => {
      invalidateBillingQueries(queryClient);
    },
  });
}

export function useUtilityBillHistory(billId: string) {
  return useQuery<UtilityBillHistory>({
    queryKey: ['billing', 'utility-bill-history', billId],
    queryFn: async () => {
      const response = await apiClient.get<unknown>(`/utility-bills/${billId}/history`);
      return normalizeUtilityBillHistory(response.data);
    },
    enabled: Boolean(billId),
  });
}
