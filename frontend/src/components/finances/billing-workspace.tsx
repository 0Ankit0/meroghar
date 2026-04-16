'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  CreditCard,
  FileClock,
  FileText,
  History,
  Plus,
  Receipt,
  Scale,
  Send,
  Upload,
  Wallet,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { Button, ConfirmDialog, Input, Skeleton } from '@/components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useBookings } from '@/hooks/use-bookings';
import {
  useCreateAdditionalCharge,
  useCreateUtilityBill,
  useDisputeAdditionalCharge,
  useDisputeBillShare,
  useDownloadInvoiceReceipt,
  useInvoice,
  useInvoices,
  usePartialPayInvoice,
  usePayBillShare,
  usePayInvoice,
  usePaymentProviders,
  usePropertyUtilityBills,
  usePublishUtilityBill,
  useRentLedger,
  useResolveAdditionalCharge,
  useResolveBillShareDispute,
  useTenantBillShares,
  useUploadUtilityBillAttachment,
  useUtilityBillHistory,
  useConfigureUtilityBillSplits,
} from '@/hooks/use-finances';
import { useLandlordListings } from '@/hooks/use-properties';
import { hasBookingViewAccess } from '@/lib/bookings';
import {
  additionalChargeStatusTone,
  disputeStatusTone,
  formatInvoiceType,
  formatSplitMethod,
  formatUtilityBillType,
  hasBillingManagementAccess,
  hasTenantBillingAccess,
  invoiceStatusTone,
  splitStatusTone,
  utilityBillStatusTone,
} from '@/lib/finances';
import { formatMoney } from '@/lib/properties';
import { useAuthStore } from '@/store/auth-store';
import type {
  AdditionalChargeRecord,
  BookingRecord,
  InitiatePaymentResponse,
  InvoiceRecord,
  PaymentProvider,
  PropertySummary,
  UtilityBillDisputeStatus,
  UtilityBillRecord,
  UtilityBillShareRecord,
  UtilityBillSplitMethod,
} from '@/types';

type WorkspaceMode = 'tenant' | 'management';

type SplitDraftRow = {
  tenantUserId: string;
  bookingIds: string[];
  bookingNumbers: string[];
  enabled: boolean;
  splitMethod: UtilityBillSplitMethod;
  splitPercent: string;
  assignedAmount: string;
};

const FALLBACK_PROVIDER: PaymentProvider = 'khalti';
const BILLING_BOOKING_STATUSES = new Set(['confirmed', 'active', 'pending_closure', 'closed']);
const EMPTY_INVOICES: InvoiceRecord[] = [];
const EMPTY_BILL_SHARES: UtilityBillShareRecord[] = [];
const EMPTY_BOOKINGS: BookingRecord[] = [];
const EMPTY_PROPERTIES: PropertySummary[] = [];
const EMPTY_UTILITY_BILLS: UtilityBillRecord[] = [];

function formatDate(value?: string | null, options?: Intl.DateTimeFormatOptions): string {
  if (!value) {
    return '—';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString(undefined, options);
}

function formatDateOnly(value?: string | null): string {
  return formatDate(value, { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatBillingWindow(start?: string | null, end?: string | null): string {
  if (!start && !end) {
    return 'Flexible period';
  }

  return `${formatDateOnly(start)} → ${formatDateOnly(end)}`;
}

function parseNumericInput(value: string): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length) {
      return detail
        .map((item) => {
          if (typeof item === 'string') {
            return item;
          }
          if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
            return item.msg;
          }
          return JSON.stringify(item);
        })
        .join(', ');
    }
  }

  return error instanceof Error && error.message ? error.message : fallback;
}

function downloadTextFile(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

function submitHiddenForm(action: string, fields: Record<string, unknown>) {
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = action;
  form.target = '_self';

  Object.entries(fields).forEach(([name, value]) => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = String(value ?? '');
    form.appendChild(input);
  });

  document.body.appendChild(form);
  form.submit();
}

function redirectToHostedPayment(response: InitiatePaymentResponse) {
  if (response.provider === 'esewa' && response.extra?.form_fields) {
    const formAction =
      (typeof response.extra.form_action === 'string' && response.extra.form_action) ||
      'https://rc-epay.esewa.com.np/api/epay/main/v2/form';
    submitHiddenForm(formAction, response.extra.form_fields as Record<string, unknown>);
    return;
  }

  if (response.payment_url) {
    window.location.href = response.payment_url;
  }
}

function buildPaymentPayload(provider: PaymentProvider, amount?: number | null) {
  return {
    provider,
    amount: amount ?? undefined,
    return_url: `${window.location.origin}/payment-callback?provider=${provider}`,
    website_url: window.location.origin,
  };
}

function isBillingRelevantBooking(booking: BookingRecord): boolean {
  return BILLING_BOOKING_STATUSES.has(booking.status.toLowerCase());
}

function bookingOverlapsBill(booking: BookingRecord, bill: UtilityBillRecord): boolean {
  const bookingStart = new Date(booking.rental_start_at).getTime();
  const bookingEnd = new Date(booking.rental_end_at).getTime();
  const billStart = new Date(`${bill.period_start}T00:00:00`).getTime();
  const billEnd = new Date(`${bill.period_end}T23:59:59`).getTime();

  if (
    Number.isNaN(bookingStart) ||
    Number.isNaN(bookingEnd) ||
    Number.isNaN(billStart) ||
    Number.isNaN(billEnd)
  ) {
    return false;
  }

  return bookingStart <= billEnd && bookingEnd >= billStart;
}

function buildSplitRows(selectedBill: UtilityBillRecord | undefined, bookings: BookingRecord[]): SplitDraftRow[] {
  if (!selectedBill) {
    return [];
  }

  const bookingMap = new Map<
    string,
    {
      bookingIds: string[];
      bookingNumbers: string[];
    }
  >();

  bookings
    .filter((booking) => bookingOverlapsBill(booking, selectedBill))
    .forEach((booking) => {
      const existing = bookingMap.get(booking.tenant_user_id);
      if (existing) {
        existing.bookingIds.push(booking.id);
        existing.bookingNumbers.push(booking.booking_number);
        return;
      }

      bookingMap.set(booking.tenant_user_id, {
        bookingIds: [booking.id],
        bookingNumbers: [booking.booking_number],
      });
    });

  const rows = new Map<string, SplitDraftRow>();

  bookingMap.forEach((value, tenantUserId) => {
    rows.set(tenantUserId, {
      tenantUserId,
      bookingIds: value.bookingIds,
      bookingNumbers: value.bookingNumbers,
      enabled: true,
      splitMethod: 'equal',
      splitPercent: '',
      assignedAmount: '',
    });
  });

  selectedBill.splits.forEach((split) => {
    const existing = rows.get(split.tenant_user_id);
    rows.set(split.tenant_user_id, {
      tenantUserId: split.tenant_user_id,
      bookingIds: existing?.bookingIds ?? [],
      bookingNumbers: existing?.bookingNumbers ?? [],
      enabled: true,
      splitMethod: split.split_method,
      splitPercent: split.split_percent?.toString() ?? '',
      assignedAmount:
        split.split_method === 'fixed' || split.split_method === 'single'
          ? split.assigned_amount.toString()
          : '',
    });
  });

  return Array.from(rows.values()).sort((left, right) => left.tenantUserId.localeCompare(right.tenantUserId));
}

function MetricCard({
  label,
  value,
  description,
  icon: Icon,
}: {
  label: string;
  value: string;
  description: string;
  icon: LucideIcon;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-gray-500">{label}</p>
            <p className="mt-2 text-2xl font-semibold text-gray-900">{value}</p>
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          </div>
          <div className="rounded-2xl bg-blue-50 p-3 text-blue-600">
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatusBadge({ label, tone }: { label: string; tone: string }) {
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${tone}`}>
      {label}
    </span>
  );
}

function EmptyCard({
  title,
  description,
  icon: Icon,
}: {
  title: string;
  description: string;
  icon: LucideIcon;
}) {
  return (
    <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center">
      <Icon className="mx-auto h-10 w-10 text-gray-300" />
      <p className="mt-4 text-lg font-medium text-gray-900">{title}</p>
      <p className="mt-2 text-sm text-gray-500">{description}</p>
    </div>
  );
}

function AttachmentPreviewList({
  attachments,
  title = 'Attachments',
}: {
  attachments: UtilityBillRecord['attachments'];
  title?: string;
}) {
  if (!attachments.length) {
    return (
      <div className="rounded-2xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500">
        No billing evidence uploaded yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm font-semibold text-gray-900">{title}</p>
      {attachments.map((attachment) => {
        const isImage = attachment.file_type.startsWith('image/');
        const isPdf = attachment.file_type === 'application/pdf';

        return (
          <div key={attachment.id} className="rounded-2xl border border-gray-200 p-4">
            {isImage ? (
              <img
                src={attachment.file_url}
                alt={`Attachment ${attachment.id}`}
                className="h-44 w-full rounded-xl object-cover"
              />
            ) : isPdf ? (
              <iframe
                title={`Attachment ${attachment.id}`}
                src={attachment.file_url}
                className="h-64 w-full rounded-xl border border-gray-200"
              />
            ) : (
              <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 text-sm text-gray-500">
                Preview unavailable for this file type.
              </div>
            )}
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm text-gray-500">
                <p>{attachment.file_type}</p>
                <p>Uploaded {formatDate(attachment.uploaded_at)}</p>
              </div>
              <a
                href={attachment.file_url}
                target="_blank"
                rel="noreferrer"
                className="text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                Open file
              </a>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function ActivityTimeline({
  entries,
  emptyState,
}: {
  entries: Array<{ event_type: string; message: string; occurred_at: string }>;
  emptyState: string;
}) {
  if (!entries.length) {
    return <p className="text-sm text-gray-500">{emptyState}</p>;
  }

  return (
    <div className="space-y-4">
      {entries.map((entry) => (
        <div key={`${entry.event_type}-${entry.occurred_at}`} className="flex gap-3">
          <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-50 text-blue-600">
            <History className="h-4 w-4" />
          </div>
          <div className="min-w-0 rounded-2xl border border-gray-200 px-4 py-3">
            <p className="text-sm font-semibold text-gray-900">{entry.message}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.16em] text-gray-400">{entry.event_type}</p>
            <p className="mt-1 text-sm text-gray-500">{formatDate(entry.occurred_at)}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function InvoiceListCard({
  title,
  description,
  invoices,
  selectedInvoiceId,
  onSelect,
  isLoading,
  error,
}: {
  title: string;
  description: string;
  invoices: InvoiceRecord[];
  selectedInvoiceId: string;
  onSelect: (invoiceId: string) => void;
  isLoading: boolean;
  error: unknown;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((key) => (
              <Skeleton key={key} className="h-14 w-full rounded-xl" />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
            {getErrorMessage(error, 'Unable to load invoices right now.')}
          </div>
        ) : invoices.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px]">
              <thead>
                <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                  <th className="pb-3 font-medium">Invoice</th>
                  <th className="pb-3 font-medium">Type</th>
                  <th className="pb-3 font-medium">Due</th>
                  <th className="pb-3 font-medium">Outstanding</th>
                  <th className="pb-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr
                    key={invoice.id}
                    className={`cursor-pointer border-b border-gray-100 last:border-0 ${
                      invoice.id === selectedInvoiceId ? 'bg-blue-50/70' : 'hover:bg-gray-50'
                    }`}
                    onClick={() => onSelect(invoice.id)}
                  >
                    <td className="py-4">
                      <p className="font-medium text-gray-900">{invoice.invoice_number}</p>
                      <p className="mt-1 text-xs text-gray-500">{invoice.id}</p>
                    </td>
                    <td className="py-4 text-sm text-gray-600">{formatInvoiceType(invoice.invoice_type)}</td>
                    <td className="py-4 text-sm text-gray-600">{formatDateOnly(invoice.due_date)}</td>
                    <td className="py-4 text-sm font-medium text-gray-900">
                      {formatMoney(invoice.outstanding_amount, invoice.currency)}
                    </td>
                    <td className="py-4">
                      <StatusBadge
                        label={formatInvoiceType(invoice.status)}
                        tone={invoiceStatusTone(invoice.status)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyCard
            title="No invoices yet"
            description="Invoices will appear here after rent schedules or bill shares are published."
            icon={Receipt}
          />
        )}
      </CardContent>
    </Card>
  );
}

function InvoiceDetailCard({
  title,
  invoice,
  isLoading,
  error,
  paymentProviders,
  paymentProvider,
  onPaymentProviderChange,
  partialAmount,
  onPartialAmountChange,
  onPayFull,
  onPayPartial,
  onDownloadReceipt,
  isPayingFull,
  isPayingPartial,
  isDownloadingReceipt,
}: {
  title: string;
  invoice?: InvoiceRecord;
  isLoading: boolean;
  error: unknown;
  paymentProviders: PaymentProvider[];
  paymentProvider: PaymentProvider;
  onPaymentProviderChange?: (provider: PaymentProvider) => void;
  partialAmount?: string;
  onPartialAmountChange?: (value: string) => void;
  onPayFull?: () => void;
  onPayPartial?: () => void;
  onDownloadReceipt?: () => void;
  isPayingFull?: boolean;
  isPayingPartial?: boolean;
  isDownloadingReceipt?: boolean;
}) {
  const canPay = Boolean(onPayFull && onPayPartial && onPaymentProviderChange && onPartialAmountChange);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription>
          Line items, reminder state, payment history, and receipt access for the selected invoice.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((key) => (
              <Skeleton key={key} className="h-16 w-full rounded-xl" />
            ))}
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
            {getErrorMessage(error, 'Unable to load the selected invoice.')}
          </div>
        ) : !invoice ? (
          <EmptyCard
            title="Select an invoice"
            description="Choose any invoice to review line items, payment progress, and reminders."
            icon={Receipt}
          />
        ) : (
          <div className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-gray-200 bg-gray-50 p-4">
              <div>
                <div className="flex flex-wrap items-center gap-3">
                  <h3 className="text-lg font-semibold text-gray-900">{invoice.invoice_number}</h3>
                  <StatusBadge
                    label={formatInvoiceType(invoice.status)}
                    tone={invoiceStatusTone(invoice.status)}
                  />
                </div>
                <p className="mt-2 text-sm text-gray-500">
                  {formatInvoiceType(invoice.invoice_type)} · Due {formatDateOnly(invoice.due_date)}
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Period {formatBillingWindow(invoice.period_start, invoice.period_end)}
                </p>
                {invoice.booking_id ? (
                  <Link
                    href={`/bookings/${invoice.booking_id}`}
                    className="mt-2 inline-flex text-sm font-medium text-blue-600 hover:text-blue-700"
                  >
                    Open related booking
                  </Link>
                ) : null}
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Outstanding</p>
                <p className="mt-1 text-2xl font-semibold text-gray-900">
                  {formatMoney(invoice.outstanding_amount, invoice.currency)}
                </p>
                <p className="mt-1 text-sm text-gray-500">
                  Paid {formatMoney(invoice.paid_amount, invoice.currency)}
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-gray-200 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.16em] text-gray-400">Subtotal</p>
                <p className="mt-1 text-sm font-semibold text-gray-900">
                  {formatMoney(invoice.subtotal, invoice.currency)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.16em] text-gray-400">Tax</p>
                <p className="mt-1 text-sm font-semibold text-gray-900">
                  {formatMoney(invoice.tax_amount, invoice.currency)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.16em] text-gray-400">Total</p>
                <p className="mt-1 text-sm font-semibold text-gray-900">
                  {formatMoney(invoice.total_amount, invoice.currency)}
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200">
              <div className="border-b border-gray-200 px-4 py-3">
                <p className="text-sm font-semibold text-gray-900">Line items</p>
              </div>
              <div className="divide-y divide-gray-100">
                {invoice.line_items.length ? (
                  invoice.line_items.map((item) => (
                    <div key={item.id} className="flex flex-wrap items-start justify-between gap-3 px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900">{item.description}</p>
                        <p className="mt-1 text-sm text-gray-500">{formatInvoiceType(item.line_item_type)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          {formatMoney(item.amount, invoice.currency)}
                        </p>
                        <p className="mt-1 text-xs text-gray-400">
                          Tax {formatMoney(item.tax_amount, invoice.currency)}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="px-4 py-4 text-sm text-gray-500">No line items have been recorded yet.</p>
                )}
              </div>
            </div>

            {canPay ? (
              <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-blue-900">
                  <CreditCard className="h-4 w-4" />
                  Start checkout
                </div>
                <div className="mt-4 grid gap-4 md:grid-cols-[0.8fr,1.2fr]">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-700" htmlFor="invoice-provider">
                      Payment provider
                    </label>
                    <select
                      id="invoice-provider"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                      value={paymentProvider}
                      onChange={(event) =>
                        onPaymentProviderChange?.(event.target.value as PaymentProvider)
                      }
                    >
                      {paymentProviders.map((provider) => (
                        <option key={provider} value={provider}>
                          {provider}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-blue-700">
                      Full payment uses the outstanding balance automatically.
                    </p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-[1fr,auto,auto]">
                    <Input
                      id="invoice-partial-amount"
                      type="number"
                      min="0"
                      step="0.01"
                      value={partialAmount}
                      onChange={(event) => onPartialAmountChange?.(event.target.value)}
                      label="Partial amount"
                    />
                    <Button
                      className="self-end"
                      onClick={onPayFull}
                      isLoading={isPayingFull}
                      disabled={invoice.outstanding_amount <= 0}
                    >
                      <Wallet className="mr-2 h-4 w-4" />
                      Pay full
                    </Button>
                    <Button
                      className="self-end"
                      variant="outline"
                      onClick={onPayPartial}
                      isLoading={isPayingPartial}
                      disabled={invoice.outstanding_amount <= 0}
                    >
                      <Scale className="mr-2 h-4 w-4" />
                      Pay partial
                    </Button>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-semibold text-gray-900">Receipt and payment audit</p>
              {onDownloadReceipt ? (
                <Button
                  variant="outline"
                  onClick={onDownloadReceipt}
                  isLoading={isDownloadingReceipt}
                  disabled={invoice.paid_amount <= 0}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Download receipt
                </Button>
              ) : null}
            </div>

            <div className="rounded-2xl border border-gray-200">
              <div className="border-b border-gray-200 px-4 py-3">
                <p className="text-sm font-semibold text-gray-900">Payments</p>
              </div>
              <div className="divide-y divide-gray-100">
                {invoice.payments.length ? (
                  invoice.payments.map((payment) => (
                    <div key={payment.id} className="flex flex-wrap items-start justify-between gap-3 px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900">{payment.payment_method}</p>
                        <p className="mt-1 text-sm text-gray-500">{formatDate(payment.created_at)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-900">
                          {formatMoney(payment.amount, payment.currency)}
                        </p>
                        <StatusBadge
                          label={formatInvoiceType(payment.status)}
                          tone={invoiceStatusTone(payment.status)}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="px-4 py-4 text-sm text-gray-500">No payment attempts have been recorded yet.</p>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200">
              <div className="border-b border-gray-200 px-4 py-3">
                <p className="text-sm font-semibold text-gray-900">Reminder cadence</p>
              </div>
              <div className="divide-y divide-gray-100">
                {invoice.reminders.length ? (
                  invoice.reminders.map((reminder) => (
                    <div key={reminder.id} className="flex flex-wrap items-start justify-between gap-3 px-4 py-3">
                      <div>
                        <p className="font-medium text-gray-900">{formatInvoiceType(reminder.reminder_type)}</p>
                        <p className="mt-1 text-sm text-gray-500">
                          Scheduled {formatDate(reminder.scheduled_for)}
                        </p>
                      </div>
                      <StatusBadge
                        label={formatInvoiceType(reminder.status)}
                        tone={invoiceStatusTone(reminder.status)}
                      />
                    </div>
                  ))
                ) : (
                  <p className="px-4 py-4 text-sm text-gray-500">No reminder entries are available.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function TenantBillingView({ paymentProviders }: { paymentProviders: PaymentProvider[] }) {
  const user = useAuthStore((state) => state.user);
  const canViewBookings = hasBookingViewAccess(user?.roles, user?.is_superuser);

  const invoicesQuery = useInvoices({ page: 1, per_page: 50 });
  const billSharesQuery = useTenantBillShares();
  const bookingsQuery = useBookings({ page: 1, per_page: 50 });

  const [selectedInvoiceId, setSelectedInvoiceId] = useState('');
  const [selectedShareId, setSelectedShareId] = useState('');
  const [selectedBookingId, setSelectedBookingId] = useState('');
  const [paymentProvider, setPaymentProvider] = useState<PaymentProvider>(FALLBACK_PROVIDER);
  const [partialAmount, setPartialAmount] = useState('');
  const [activeShareDisputeId, setActiveShareDisputeId] = useState<string | null>(null);
  const [shareDisputeReason, setShareDisputeReason] = useState('');
  const [activeChargeDisputeId, setActiveChargeDisputeId] = useState<string | null>(null);
  const [chargeDisputeReason, setChargeDisputeReason] = useState('');

  const payInvoice = usePayInvoice();
  const partialPayInvoice = usePartialPayInvoice();
  const downloadReceipt = useDownloadInvoiceReceipt();
  const payBillShare = usePayBillShare();
  const disputeBillShare = useDisputeBillShare();
  const disputeAdditionalCharge = useDisputeAdditionalCharge();

  const invoices = invoicesQuery.data?.items ?? EMPTY_INVOICES;
  const billShares = billSharesQuery.data?.items ?? EMPTY_BILL_SHARES;
  const bookings = bookingsQuery.data?.items ?? EMPTY_BOOKINGS;

  useEffect(() => {
    const nextProvider = paymentProviders[0] ?? FALLBACK_PROVIDER;
    if (!paymentProviders.includes(paymentProvider)) {
      setPaymentProvider(nextProvider);
    }
  }, [paymentProvider, paymentProviders]);

  useEffect(() => {
    if (!invoices.length) {
      setSelectedInvoiceId('');
      return;
    }

    if (!invoices.some((invoice) => invoice.id === selectedInvoiceId)) {
      setSelectedInvoiceId(invoices[0]?.id ?? '');
    }
  }, [invoices, selectedInvoiceId]);

  useEffect(() => {
    if (!billShares.length) {
      setSelectedShareId('');
      return;
    }

    if (!billShares.some((share) => share.split.id === selectedShareId)) {
      setSelectedShareId(billShares[0]?.split.id ?? '');
    }
  }, [billShares, selectedShareId]);

  useEffect(() => {
    if (!bookings.length) {
      setSelectedBookingId('');
      return;
    }

    if (!bookings.some((booking) => booking.id === selectedBookingId)) {
      setSelectedBookingId(bookings[0]?.id ?? '');
    }
  }, [bookings, selectedBookingId]);

  const invoiceDetailQuery = useInvoice(selectedInvoiceId);
  const selectedInvoice =
    invoiceDetailQuery.data ?? invoices.find((invoice) => invoice.id === selectedInvoiceId);
  const selectedInvoiceOutstanding = selectedInvoice?.outstanding_amount;
  const selectedInvoiceKey = selectedInvoice?.id;

  useEffect(() => {
    if (selectedInvoiceKey) {
      setPartialAmount((selectedInvoiceOutstanding ?? 0).toFixed(2));
    }
  }, [selectedInvoiceKey, selectedInvoiceOutstanding]);

  const selectedShare = billShares.find((share) => share.split.id === selectedShareId);
  const shareHistoryQuery = useUtilityBillHistory(selectedShare?.bill.id ?? '');
  const ledgerQuery = useRentLedger(selectedBookingId);

  const outstandingInvoices = useMemo(
    () => invoices.reduce((sum, invoice) => sum + invoice.outstanding_amount, 0),
    [invoices],
  );
  const outstandingBillShares = useMemo(
    () => billShares.reduce((sum, share) => sum + share.split.outstanding_amount, 0),
    [billShares],
  );
  const dueNowCount = useMemo(
    () => invoices.filter((invoice) => invoice.outstanding_amount > 0).length + billShares.filter((share) => share.split.outstanding_amount > 0).length,
    [billShares, invoices],
  );

  const actionError = useMemo(() => {
    const errorSource =
      payInvoice.error ??
      partialPayInvoice.error ??
      downloadReceipt.error ??
      payBillShare.error ??
      disputeBillShare.error ??
      disputeAdditionalCharge.error;

    return errorSource ? getErrorMessage(errorSource, 'Unable to complete that billing action right now.') : null;
  }, [
    disputeAdditionalCharge.error,
    disputeBillShare.error,
    downloadReceipt.error,
    partialPayInvoice.error,
    payBillShare.error,
    payInvoice.error,
  ]);

  const handleInvoicePayment = (mode: 'full' | 'partial') => {
    if (!selectedInvoice) {
      return;
    }

    const paymentAmount =
      mode === 'partial' ? parseNumericInput(partialAmount) : selectedInvoice.outstanding_amount;

    if (mode === 'partial' && (!paymentAmount || paymentAmount <= 0)) {
      return;
    }

    const mutation = mode === 'partial' ? partialPayInvoice : payInvoice;
    mutation.mutate(
      {
        invoiceId: selectedInvoice.id,
        data: buildPaymentPayload(paymentProvider, mode === 'partial' ? paymentAmount : undefined),
      },
      {
        onSuccess: (response) => {
          redirectToHostedPayment(response);
        },
      },
    );
  };

  const handleReceiptDownload = () => {
    if (!selectedInvoice) {
      return;
    }

    downloadReceipt.mutate(selectedInvoice.id, {
      onSuccess: ({ content, filename }) => {
        downloadTextFile(content, filename);
      },
    });
  };

  const handleBillSharePayment = () => {
    if (!selectedShare || selectedShare.split.outstanding_amount <= 0) {
      return;
    }

    payBillShare.mutate(
      {
        billShareId: selectedShare.split.id,
        data: buildPaymentPayload(paymentProvider, selectedShare.split.outstanding_amount),
      },
      {
        onSuccess: (response) => {
          redirectToHostedPayment(response);
        },
      },
    );
  };

  const handleShareDispute = () => {
    if (!activeShareDisputeId || !shareDisputeReason.trim()) {
      return;
    }

    disputeBillShare.mutate(
      {
        billShareId: activeShareDisputeId,
        data: { reason: shareDisputeReason.trim() },
      },
      {
        onSuccess: () => {
          setShareDisputeReason('');
          setActiveShareDisputeId(null);
        },
      },
    );
  };

  const handleChargeDispute = () => {
    if (!activeChargeDisputeId || !chargeDisputeReason.trim()) {
      return;
    }

    disputeAdditionalCharge.mutate(
      {
        chargeId: activeChargeDisputeId,
        data: { reason: chargeDisputeReason.trim() },
      },
      {
        onSuccess: () => {
          setChargeDisputeReason('');
          setActiveChargeDisputeId(null);
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Open invoice balance"
          value={formatMoney(outstandingInvoices)}
          description="Rent and checkout invoices still awaiting settlement."
          icon={Receipt}
        />
        <MetricCard
          label="Utility share balance"
          value={formatMoney(outstandingBillShares)}
          description="Published utility bill shares that still need action."
          icon={Zap}
        />
        <MetricCard
          label="Due items"
          value={String(dueNowCount)}
          description="Invoices and utility shares currently outstanding."
          icon={Wallet}
        />
        <MetricCard
          label="Bookings in ledger"
          value={String(bookings.length)}
          description="Rental ledgers available for rent timeline visibility."
          icon={FileClock}
        />
      </div>

      {actionError ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {actionError}
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.08fr,0.92fr]">
        <div className="space-y-6">
          <InvoiceListCard
            title="Tenant invoices"
            description="Review rent charges, overdue balances, and utility share invoices that are payable from the web workspace."
            invoices={invoices}
            selectedInvoiceId={selectedInvoiceId}
            onSelect={setSelectedInvoiceId}
            isLoading={invoicesQuery.isLoading}
            error={invoicesQuery.error}
          />

          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Utility bill shares</CardTitle>
              <CardDescription>
                Published tenant shares, disputes, and evidence-backed bill previews.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {billSharesQuery.isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((key) => (
                    <Skeleton key={key} className="h-14 w-full rounded-xl" />
                  ))}
                </div>
              ) : billSharesQuery.error ? (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
                  {getErrorMessage(billSharesQuery.error, 'Unable to load utility bill shares.')}
                </div>
              ) : billShares.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[760px]">
                    <thead>
                      <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                        <th className="pb-3 font-medium">Bill</th>
                        <th className="pb-3 font-medium">Period</th>
                        <th className="pb-3 font-medium">Assigned</th>
                        <th className="pb-3 font-medium">Outstanding</th>
                        <th className="pb-3 font-medium">Status</th>
                        <th className="pb-3 font-medium">Disputes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {billShares.map((share) => (
                        <tr
                          key={share.split.id}
                          className={`cursor-pointer border-b border-gray-100 last:border-0 ${
                            share.split.id === selectedShareId ? 'bg-blue-50/70' : 'hover:bg-gray-50'
                          }`}
                          onClick={() => setSelectedShareId(share.split.id)}
                        >
                          <td className="py-4">
                            <p className="font-medium text-gray-900">{formatUtilityBillType(share.bill.bill_type)}</p>
                            <p className="mt-1 text-xs text-gray-500">{share.bill.billing_period_label}</p>
                          </td>
                          <td className="py-4 text-sm text-gray-600">
                            {formatBillingWindow(share.bill.period_start, share.bill.period_end)}
                          </td>
                          <td className="py-4 text-sm font-medium text-gray-900">
                            {formatMoney(share.split.assigned_amount)}
                          </td>
                          <td className="py-4 text-sm font-medium text-gray-900">
                            {formatMoney(share.split.outstanding_amount)}
                          </td>
                          <td className="py-4">
                            <StatusBadge
                              label={formatInvoiceType(share.split.status)}
                              tone={splitStatusTone(share.split.status)}
                            />
                          </td>
                          <td className="py-4 text-sm text-gray-600">{share.disputes.length}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyCard
                  title="No utility shares published"
                  description="Once a landlord publishes utility splits for your property, they will appear here with evidence and payment actions."
                  icon={Zap}
                />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <InvoiceDetailCard
            title="Invoice detail"
            invoice={selectedInvoice}
            isLoading={invoiceDetailQuery.isLoading}
            error={invoiceDetailQuery.error}
            paymentProviders={paymentProviders}
            paymentProvider={paymentProvider}
            onPaymentProviderChange={setPaymentProvider}
            partialAmount={partialAmount}
            onPartialAmountChange={setPartialAmount}
            onPayFull={() => handleInvoicePayment('full')}
            onPayPartial={() => handleInvoicePayment('partial')}
            onDownloadReceipt={handleReceiptDownload}
            isPayingFull={payInvoice.isPending}
            isPayingPartial={partialPayInvoice.isPending}
            isDownloadingReceipt={downloadReceipt.isPending}
          />

          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Selected utility bill share</CardTitle>
              <CardDescription>
                Attachment preview, settlement actions, dispute history, and status timeline.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!selectedShare ? (
                <EmptyCard
                  title="Select a bill share"
                  description="Choose a utility share to inspect evidence, dispute state, and hosted payment options."
                  icon={Zap}
                />
              ) : (
                <div className="space-y-6">
                  <div className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-gray-200 bg-gray-50 p-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-lg font-semibold text-gray-900">
                          {formatUtilityBillType(selectedShare.bill.bill_type)}
                        </h3>
                        <StatusBadge
                          label={formatInvoiceType(selectedShare.split.status)}
                          tone={splitStatusTone(selectedShare.split.status)}
                        />
                      </div>
                      <p className="mt-2 text-sm text-gray-500">{selectedShare.bill.billing_period_label}</p>
                      <p className="mt-1 text-sm text-gray-500">
                        Due {formatDateOnly(selectedShare.bill.due_date)} · Split {formatSplitMethod(selectedShare.split.split_method)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Outstanding</p>
                      <p className="mt-1 text-2xl font-semibold text-gray-900">
                        {formatMoney(selectedShare.split.outstanding_amount)}
                      </p>
                      <p className="mt-1 text-sm text-gray-500">
                        Assigned {formatMoney(selectedShare.split.assigned_amount)}
                      </p>
                    </div>
                  </div>

                  <AttachmentPreviewList attachments={selectedShare.bill.attachments} title="Bill evidence" />

                  <div className="rounded-2xl border border-blue-200 bg-blue-50 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-blue-900">Pay utility share</p>
                        <p className="mt-1 text-sm text-blue-700">
                          Utility shares use the hosted billing checkout so tenants can settle from the web dashboard.
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <select
                          className="rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm text-gray-900"
                          value={paymentProvider}
                          onChange={(event) => setPaymentProvider(event.target.value as PaymentProvider)}
                        >
                          {paymentProviders.map((provider) => (
                            <option key={provider} value={provider}>
                              {provider}
                            </option>
                          ))}
                        </select>
                        <Button
                          onClick={handleBillSharePayment}
                          isLoading={payBillShare.isPending}
                          disabled={
                            selectedShare.split.outstanding_amount <= 0 ||
                            selectedShare.split.status === 'disputed'
                          }
                        >
                          <CreditCard className="mr-2 h-4 w-4" />
                          Pay share
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-gray-200 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-gray-900">Dispute workflow</p>
                        <p className="mt-1 text-sm text-gray-500">
                          Raise an issue when the bill evidence or split assignment needs review.
                        </p>
                      </div>
                      {selectedShare.split.status !== 'paid' && selectedShare.split.status !== 'waived' ? (
                        <Button
                          variant="outline"
                          onClick={() =>
                            setActiveShareDisputeId((current) =>
                              current === selectedShare.split.id ? null : selectedShare.split.id,
                            )
                          }
                        >
                          <AlertTriangle className="mr-2 h-4 w-4" />
                          {activeShareDisputeId === selectedShare.split.id ? 'Cancel dispute' : 'Raise dispute'}
                        </Button>
                      ) : null}
                    </div>

                    {activeShareDisputeId === selectedShare.split.id ? (
                      <div className="mt-4 space-y-3">
                        <label className="block text-sm font-medium text-gray-700" htmlFor="share-dispute">
                          Dispute reason
                        </label>
                        <textarea
                          id="share-dispute"
                          className="min-h-[96px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                          value={shareDisputeReason}
                          onChange={(event) => setShareDisputeReason(event.target.value)}
                          placeholder="Describe the issue with this utility bill share."
                        />
                        <Button onClick={handleShareDispute} isLoading={disputeBillShare.isPending}>
                          Submit dispute
                        </Button>
                      </div>
                    ) : null}

                    <div className="mt-4 space-y-3">
                      {selectedShare.disputes.length ? (
                        selectedShare.disputes.map((dispute) => (
                          <div key={dispute.id} className="rounded-2xl border border-gray-200 p-4">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div>
                                <p className="font-medium text-gray-900">{dispute.reason}</p>
                                <p className="mt-1 text-sm text-gray-500">
                                  Opened {formatDate(dispute.opened_at)}
                                </p>
                                {dispute.resolution_notes ? (
                                  <p className="mt-2 text-sm text-gray-600">{dispute.resolution_notes}</p>
                                ) : null}
                              </div>
                              <StatusBadge
                                label={formatInvoiceType(dispute.status)}
                                tone={disputeStatusTone(dispute.status)}
                              />
                            </div>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500">No disputes have been raised for this share.</p>
                      )}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-gray-200 p-4">
                    <p className="text-sm font-semibold text-gray-900">Settlement timeline</p>
                    <div className="mt-4">
                      {shareHistoryQuery.isLoading ? (
                        <div className="space-y-3">
                          {[1, 2].map((key) => (
                            <Skeleton key={key} className="h-16 w-full rounded-xl" />
                          ))}
                        </div>
                      ) : shareHistoryQuery.error ? (
                        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
                          {getErrorMessage(shareHistoryQuery.error, 'Unable to load bill history.')}
                        </div>
                      ) : (
                        <ActivityTimeline
                          entries={shareHistoryQuery.data?.entries ?? []}
                          emptyState="No timeline entries have been recorded yet."
                        />
                      )}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle className="text-xl">Rent ledger visibility</CardTitle>
            <CardDescription>
              Monthly rent schedule, checkout balance, and additional charge disputes for the selected booking.
            </CardDescription>
          </div>
          {canViewBookings && bookings.length ? (
            <div className="flex flex-wrap items-center gap-3">
              <select
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                value={selectedBookingId}
                onChange={(event) => setSelectedBookingId(event.target.value)}
              >
                {bookings.map((booking) => (
                  <option key={booking.id} value={booking.id}>
                    {booking.booking_number} · {booking.property.name}
                  </option>
                ))}
              </select>
              {selectedBookingId ? (
                <Link href={`/bookings/${selectedBookingId}`}>
                  <Button variant="outline">Open booking</Button>
                </Link>
              ) : null}
            </div>
          ) : null}
        </CardHeader>
        <CardContent>
          {!canViewBookings ? (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-4 text-sm text-amber-700">
              This account cannot access booking-ledger views right now.
            </div>
          ) : bookingsQuery.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((key) => (
                <Skeleton key={key} className="h-14 w-full rounded-xl" />
              ))}
            </div>
          ) : bookingsQuery.error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
              {getErrorMessage(bookingsQuery.error, 'Unable to load booking ledgers.')}
            </div>
          ) : !bookings.length ? (
            <EmptyCard
              title="No bookings found"
              description="Rent ledgers appear after a booking is confirmed."
              icon={FileClock}
            />
          ) : ledgerQuery.isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((key) => (
                <Skeleton key={key} className="h-16 w-full rounded-xl" />
              ))}
            </div>
          ) : ledgerQuery.error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
              {getErrorMessage(ledgerQuery.error, 'Unable to load the selected rent ledger.')}
            </div>
          ) : ledgerQuery.data ? (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <MetricCard
                  label="Ledger total"
                  value={formatMoney(ledgerQuery.data.total_amount, ledgerQuery.data.currency)}
                  description="Total scheduled rent for the selected booking."
                  icon={Receipt}
                />
                <MetricCard
                  label="Settled"
                  value={formatMoney(ledgerQuery.data.paid_amount, ledgerQuery.data.currency)}
                  description="Payments already credited to the booking ledger."
                  icon={CheckCircle2}
                />
                <MetricCard
                  label="Outstanding"
                  value={formatMoney(ledgerQuery.data.outstanding_amount, ledgerQuery.data.currency)}
                  description="Current unpaid balance across scheduled rent entries."
                  icon={AlertTriangle}
                />
              </div>

              <div className="rounded-2xl border border-gray-200">
                <div className="border-b border-gray-200 px-4 py-3">
                  <p className="text-sm font-semibold text-gray-900">Rent schedule</p>
                </div>
                <div className="divide-y divide-gray-100">
                  {ledgerQuery.data.entries.length ? (
                    ledgerQuery.data.entries.map((entry) => (
                      <div key={`${entry.period_start}-${entry.invoice_id ?? 'entry'}`} className="px-4 py-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-gray-900">
                              {formatBillingWindow(entry.period_start, entry.period_end)}
                            </p>
                            <p className="mt-1 text-sm text-gray-500">
                              Due {formatDateOnly(entry.due_date)}
                              {entry.invoice_id ? ` · Invoice ${entry.invoice_id}` : ''}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-semibold text-gray-900">
                              {formatMoney(entry.amount_due, ledgerQuery.data.currency)}
                            </p>
                            <p className="mt-1 text-sm text-gray-500">
                              Outstanding {formatMoney(entry.outstanding_amount, ledgerQuery.data.currency)}
                            </p>
                            {entry.invoice_status ? (
                              <div className="mt-2">
                                <StatusBadge
                                  label={formatInvoiceType(entry.invoice_status)}
                                  tone={invoiceStatusTone(entry.invoice_status)}
                                />
                              </div>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="px-4 py-4 text-sm text-gray-500">No rent schedule entries were returned.</p>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-gray-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">Checkout and additional charges</p>
                    <p className="mt-1 text-sm text-gray-500">
                      Damage and closeout charges are visible here with evidence and dispute controls.
                    </p>
                  </div>
                </div>

                <div className="mt-4 space-y-4">
                  {ledgerQuery.data.additional_charges.length ? (
                    ledgerQuery.data.additional_charges.map((charge) => {
                      const canDispute =
                        !['paid', 'waived', 'disputed'].includes(charge.status.toLowerCase());

                      return (
                        <div key={charge.id} className="rounded-2xl border border-gray-200 p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="flex flex-wrap items-center gap-3">
                                <p className="font-medium text-gray-900">{charge.description}</p>
                                <StatusBadge
                                  label={formatInvoiceType(charge.status)}
                                  tone={additionalChargeStatusTone(charge.status)}
                                />
                              </div>
                              <p className="mt-2 text-sm text-gray-500">
                                {formatInvoiceType(charge.charge_type)} · Raised {formatDate(charge.created_at)}
                              </p>
                              {charge.evidence_url ? (
                                <a
                                  href={charge.evidence_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="mt-2 inline-flex text-sm font-medium text-blue-600 hover:text-blue-700"
                                >
                                  Open evidence
                                </a>
                              ) : null}
                              {charge.dispute_reason ? (
                                <p className="mt-2 text-sm text-gray-600">Dispute: {charge.dispute_reason}</p>
                              ) : null}
                              {charge.resolution_notes ? (
                                <p className="mt-1 text-sm text-gray-600">
                                  Resolution: {charge.resolution_notes}
                                </p>
                              ) : null}
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold text-gray-900">
                                {formatMoney(charge.amount, ledgerQuery.data.currency)}
                              </p>
                              {charge.resolved_amount !== null && charge.resolved_amount !== undefined ? (
                                <p className="mt-1 text-sm text-gray-500">
                                  Resolved at {formatMoney(charge.resolved_amount, ledgerQuery.data.currency)}
                                </p>
                              ) : null}
                              {canDispute ? (
                                <Button
                                  className="mt-3"
                                  variant="outline"
                                  size="sm"
                                  onClick={() =>
                                    setActiveChargeDisputeId((current) =>
                                      current === charge.id ? null : charge.id,
                                    )
                                  }
                                >
                                  <AlertTriangle className="mr-2 h-4 w-4" />
                                  {activeChargeDisputeId === charge.id ? 'Cancel dispute' : 'Dispute charge'}
                                </Button>
                              ) : null}
                            </div>
                          </div>

                          {activeChargeDisputeId === charge.id ? (
                            <div className="mt-4 space-y-3">
                              <textarea
                                className="min-h-[96px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                                value={chargeDisputeReason}
                                onChange={(event) => setChargeDisputeReason(event.target.value)}
                                placeholder="Explain why this charge should be reviewed."
                              />
                              <Button onClick={handleChargeDispute} isLoading={disputeAdditionalCharge.isPending}>
                                Submit charge dispute
                              </Button>
                            </div>
                          ) : null}
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-sm text-gray-500">No additional charges have been posted for this booking.</p>
                  )}
                </div>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function ManagementBillingView() {
  const propertiesQuery = useLandlordListings({ page: 1, per_page: 50 });
  const bookingsQuery = useBookings({ page: 1, per_page: 50 });
  const invoicesQuery = useInvoices({ page: 1, per_page: 50 });

  const [selectedPropertyId, setSelectedPropertyId] = useState('');
  const [propertyLookupId, setPropertyLookupId] = useState('');
  const [selectedBillId, setSelectedBillId] = useState('');
  const [selectedBookingId, setSelectedBookingId] = useState('');
  const [selectedInvoiceId, setSelectedInvoiceId] = useState('');
  const [attachmentFile, setAttachmentFile] = useState<File | null>(null);
  const [attachmentInputKey, setAttachmentInputKey] = useState(0);
  const [publishDialogOpen, setPublishDialogOpen] = useState(false);
  const [splitRows, setSplitRows] = useState<SplitDraftRow[]>([]);
  const [splitError, setSplitError] = useState<string | null>(null);
  const [activeSplitResolveId, setActiveSplitResolveId] = useState<string | null>(null);
  const [splitResolutionOutcome, setSplitResolutionOutcome] = useState<UtilityBillDisputeStatus>('resolved');
  const [splitResolutionNotes, setSplitResolutionNotes] = useState('');
  const [activeChargeResolveId, setActiveChargeResolveId] = useState<string | null>(null);
  const [chargeResolutionOutcome, setChargeResolutionOutcome] =
    useState<AdditionalChargeRecord['status']>('accepted');
  const [chargeResolvedAmount, setChargeResolvedAmount] = useState('');
  const [chargeResolutionNotes, setChargeResolutionNotes] = useState('');

  const [billType, setBillType] = useState('electricity');
  const [billingPeriodLabel, setBillingPeriodLabel] = useState('');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [ownerSubsidyAmount, setOwnerSubsidyAmount] = useState('');
  const [billNotes, setBillNotes] = useState('');

  const [chargeType, setChargeType] = useState('damage');
  const [chargeDescription, setChargeDescription] = useState('');
  const [chargeAmount, setChargeAmount] = useState('');
  const [chargeEvidenceUrl, setChargeEvidenceUrl] = useState('');

  const createUtilityBill = useCreateUtilityBill();
  const uploadAttachment = useUploadUtilityBillAttachment();
  const configureSplits = useConfigureUtilityBillSplits();
  const publishUtilityBill = usePublishUtilityBill();
  const resolveBillShareDispute = useResolveBillShareDispute();
  const createAdditionalCharge = useCreateAdditionalCharge();
  const resolveAdditionalCharge = useResolveAdditionalCharge();
  const downloadReceipt = useDownloadInvoiceReceipt();

  const propertyOptions = propertiesQuery.data?.items ?? EMPTY_PROPERTIES;
  const managementBookings = bookingsQuery.data?.items ?? EMPTY_BOOKINGS;

  useEffect(() => {
    if (!selectedPropertyId && propertyOptions.length) {
      setSelectedPropertyId(propertyOptions[0]?.id ?? '');
    }
  }, [propertyOptions, selectedPropertyId]);

  const billsQuery = usePropertyUtilityBills(selectedPropertyId, { page: 1, per_page: 50 });
  const bills = billsQuery.data?.items ?? EMPTY_UTILITY_BILLS;
  const managementInvoices = invoicesQuery.data?.items ?? EMPTY_INVOICES;

  useEffect(() => {
    if (!bills.length) {
      setSelectedBillId('');
      return;
    }

    if (!bills.some((bill) => bill.id === selectedBillId)) {
      setSelectedBillId(bills[0]?.id ?? '');
    }
  }, [bills, selectedBillId]);

  const selectedBill = bills.find((bill) => bill.id === selectedBillId);
  const billHistoryQuery = useUtilityBillHistory(selectedBillId);

  const propertyBookings = useMemo(
    () =>
      managementBookings.filter(
        (booking) => booking.property.id === selectedPropertyId && isBillingRelevantBooking(booking),
      ),
    [managementBookings, selectedPropertyId],
  );

  useEffect(() => {
    if (!propertyBookings.length) {
      setSelectedBookingId('');
      return;
    }

    if (!propertyBookings.some((booking) => booking.id === selectedBookingId)) {
      setSelectedBookingId(propertyBookings[0]?.id ?? '');
    }
  }, [propertyBookings, selectedBookingId]);

  const ledgerQuery = useRentLedger(selectedBookingId);

  useEffect(() => {
    if (!managementInvoices.length) {
      setSelectedInvoiceId('');
      return;
    }

    if (!managementInvoices.some((invoice) => invoice.id === selectedInvoiceId)) {
      setSelectedInvoiceId(managementInvoices[0]?.id ?? '');
    }
  }, [managementInvoices, selectedInvoiceId]);

  const invoiceDetailQuery = useInvoice(selectedInvoiceId);
  const selectedInvoice =
    invoiceDetailQuery.data ?? managementInvoices.find((invoice) => invoice.id === selectedInvoiceId);

  useEffect(() => {
    setSplitRows(buildSplitRows(selectedBill, propertyBookings));
    setSplitError(null);
  }, [propertyBookings, selectedBill]);

  const outstandingInvoices = useMemo(
    () => managementInvoices.reduce((sum, invoice) => sum + invoice.outstanding_amount, 0),
    [managementInvoices],
  );

  const propertyTenantCount = useMemo(
    () => new Set(propertyBookings.map((booking) => booking.tenant_user_id)).size,
    [propertyBookings],
  );

  const publishedBillCount = bills.filter((bill) => bill.published_at).length;

  const managementActionError = useMemo(() => {
    const errorSource =
      createUtilityBill.error ??
      uploadAttachment.error ??
      configureSplits.error ??
      publishUtilityBill.error ??
      resolveBillShareDispute.error ??
      createAdditionalCharge.error ??
      resolveAdditionalCharge.error ??
      downloadReceipt.error;

    return errorSource
      ? getErrorMessage(errorSource, 'Unable to complete that billing management action right now.')
      : null;
  }, [
    configureSplits.error,
    createAdditionalCharge.error,
    createUtilityBill.error,
    downloadReceipt.error,
    publishUtilityBill.error,
    resolveAdditionalCharge.error,
    resolveBillShareDispute.error,
    uploadAttachment.error,
  ]);

  const handlePropertyLookup = () => {
    if (propertyLookupId.trim()) {
      setSelectedPropertyId(propertyLookupId.trim());
    }
  };

  const handleCreateBill = () => {
    if (!selectedPropertyId) {
      return;
    }

    const parsedTotalAmount = parseNumericInput(totalAmount);
    const parsedOwnerSubsidy = parseNumericInput(ownerSubsidyAmount);
    if (!parsedTotalAmount || parsedTotalAmount <= 0) {
      return;
    }

    createUtilityBill.mutate(
      {
        propertyId: selectedPropertyId,
        data: {
          bill_type: billType,
          billing_period_label: billingPeriodLabel.trim(),
          period_start: periodStart,
          period_end: periodEnd,
          due_date: dueDate,
          total_amount: parsedTotalAmount,
          owner_subsidy_amount: parsedOwnerSubsidy ?? 0,
          notes: billNotes.trim(),
        },
      },
      {
        onSuccess: (bill) => {
          setSelectedBillId(bill.id);
          setBillingPeriodLabel('');
          setPeriodStart('');
          setPeriodEnd('');
          setDueDate('');
          setTotalAmount('');
          setOwnerSubsidyAmount('');
          setBillNotes('');
        },
      },
    );
  };

  const handleAttachmentUpload = () => {
    if (!selectedBill || !attachmentFile) {
      return;
    }

    uploadAttachment.mutate(
      {
        billId: selectedBill.id,
        data: { file: attachmentFile },
      },
      {
        onSuccess: () => {
          setAttachmentFile(null);
          setAttachmentInputKey((current) => current + 1);
        },
      },
    );
  };

  const handleAutoSplit = (method: UtilityBillSplitMethod) => {
    if (!selectedBill) {
      return;
    }

    configureSplits.mutate({
      billId: selectedBill.id,
      data: {
        default_method: method,
        splits: [],
      },
    });
  };

  const handleSaveManualSplits = () => {
    if (!selectedBill) {
      return;
    }

    const enabledRows = splitRows.filter((row) => row.enabled);
    if (!enabledRows.length) {
      setSplitError('Select at least one tenant share before saving the split configuration.');
      return;
    }

    if (enabledRows.some((row) => row.splitMethod === 'single') && enabledRows.length !== 1) {
      setSplitError('Single split mode can only be used for one tenant entry.');
      return;
    }

    const splits = enabledRows.map((row) => {
      const split = {
        tenant_user_id: row.tenantUserId,
        split_method: row.splitMethod,
      } as {
        tenant_user_id: string;
        split_method: UtilityBillSplitMethod;
        split_percent?: number;
        assigned_amount?: number;
      };

      if (row.splitMethod === 'percentage') {
        const splitPercent = parseNumericInput(row.splitPercent);
        if (splitPercent !== null) {
          split.split_percent = splitPercent;
        }
      }

      if (row.splitMethod === 'fixed') {
        const assignedAmount = parseNumericInput(row.assignedAmount);
        if (assignedAmount !== null) {
          split.assigned_amount = assignedAmount;
        }
      }

      return split;
    });

    setSplitError(null);
    configureSplits.mutate({
      billId: selectedBill.id,
      data: {
        default_method: null,
        splits,
      },
    });
  };

  const handlePublishBill = () => {
    if (!selectedBill) {
      return;
    }

    publishUtilityBill.mutate(selectedBill.id, {
      onSuccess: () => {
        setPublishDialogOpen(false);
      },
    });
  };

  const handleResolveSplitDispute = () => {
    if (!activeSplitResolveId) {
      return;
    }

    resolveBillShareDispute.mutate(
      {
        billShareId: activeSplitResolveId,
        data: {
          outcome: splitResolutionOutcome,
          resolution_notes: splitResolutionNotes.trim(),
        },
      },
      {
        onSuccess: () => {
          setActiveSplitResolveId(null);
          setSplitResolutionNotes('');
          setSplitResolutionOutcome('resolved');
        },
      },
    );
  };

  const handleCreateAdditionalCharge = () => {
    if (!selectedBookingId) {
      return;
    }

    const amount = parseNumericInput(chargeAmount);
    if (!amount || amount <= 0 || !chargeDescription.trim()) {
      return;
    }

    createAdditionalCharge.mutate(
      {
        bookingId: selectedBookingId,
        data: {
          charge_type: chargeType,
          description: chargeDescription.trim(),
          amount,
          evidence_url: chargeEvidenceUrl.trim(),
        },
      },
      {
        onSuccess: () => {
          setChargeDescription('');
          setChargeAmount('');
          setChargeEvidenceUrl('');
        },
      },
    );
  };

  const handleResolveCharge = () => {
    if (!activeChargeResolveId) {
      return;
    }

    const resolvedAmount = parseNumericInput(chargeResolvedAmount);

    resolveAdditionalCharge.mutate(
      {
        chargeId: activeChargeResolveId,
        data: {
          outcome: chargeResolutionOutcome,
          resolved_amount: resolvedAmount ?? undefined,
          resolution_notes: chargeResolutionNotes.trim(),
        },
      },
      {
        onSuccess: () => {
          setActiveChargeResolveId(null);
          setChargeResolutionOutcome('accepted');
          setChargeResolvedAmount('');
          setChargeResolutionNotes('');
        },
      },
    );
  };

  const handleReceiptDownload = () => {
    if (!selectedInvoice) {
      return;
    }

    downloadReceipt.mutate(selectedInvoice.id, {
      onSuccess: ({ content, filename }) => {
        downloadTextFile(content, filename);
      },
    });
  };

  const disputedSplits = selectedBill?.splits.filter((split) => split.status === 'disputed') ?? [];
  const selectedChargeList = ledgerQuery.data?.additional_charges ?? [];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Tracked invoices"
          value={String(managementInvoices.length)}
          description="Owner-visible rent and utility-share invoices."
          icon={Receipt}
        />
        <MetricCard
          label="Outstanding invoice balance"
          value={formatMoney(outstandingInvoices)}
          description="Accessible invoices that still have unpaid balance."
          icon={Wallet}
        />
        <MetricCard
          label="Published utility bills"
          value={String(publishedBillCount)}
          description="Bills already pushed to tenants with payable shares."
          icon={Send}
        />
        <MetricCard
          label="Active property tenants"
          value={String(propertyTenantCount)}
          description="Current or recent occupants used for split configuration."
          icon={Building2}
        />
      </div>

      {managementActionError ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {managementActionError}
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Property utility billing workspace</CardTitle>
          <CardDescription>
            Choose a property, create bills, upload evidence, configure splits, and publish tenant charges from the website.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700" htmlFor="management-property">
                Managed property
              </label>
              <select
                id="management-property"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                value={selectedPropertyId}
                onChange={(event) => setSelectedPropertyId(event.target.value)}
              >
                <option value="">Select a property</option>
                {propertyOptions.map((property) => (
                  <option key={property.id} value={property.id}>
                    {property.name}
                  </option>
                ))}
              </select>
              {propertiesQuery.error ? (
                <p className="text-sm text-amber-700">
                  {getErrorMessage(
                    propertiesQuery.error,
                    'Property lookup is limited to owned listings, so use a known property ID if needed.',
                  )}
                </p>
              ) : (
                <p className="text-sm text-gray-500">
                  Only website-accessible management workflows appear here; mobile remains tenant focused.
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700" htmlFor="management-property-id">
                Open property by ID
              </label>
              <div className="flex gap-2">
                <Input
                  id="management-property-id"
                  value={propertyLookupId}
                  onChange={(event) => setPropertyLookupId(event.target.value)}
                  placeholder="Encoded property ID"
                />
                <Button variant="outline" onClick={handlePropertyLookup}>
                  Load
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {selectedPropertyId ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Create utility bill</CardTitle>
              <CardDescription>
                Capture the billing period, owner subsidy, and due date before attachments and split configuration.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 lg:grid-cols-3">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700" htmlFor="utility-bill-type">
                    Bill type
                  </label>
                  <select
                    id="utility-bill-type"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                    value={billType}
                    onChange={(event) => setBillType(event.target.value)}
                  >
                    {['electricity', 'water', 'internet', 'gas', 'other'].map((type) => (
                      <option key={type} value={type}>
                        {formatUtilityBillType(type)}
                      </option>
                    ))}
                  </select>
                </div>
                <Input
                  label="Billing label"
                  id="billing-label"
                  value={billingPeriodLabel}
                  onChange={(event) => setBillingPeriodLabel(event.target.value)}
                  placeholder="e.g. April 2026"
                />
                <Input
                  label="Due date"
                  id="billing-due-date"
                  type="date"
                  value={dueDate}
                  onChange={(event) => setDueDate(event.target.value)}
                />
                <Input
                  label="Period start"
                  id="billing-period-start"
                  type="date"
                  value={periodStart}
                  onChange={(event) => setPeriodStart(event.target.value)}
                />
                <Input
                  label="Period end"
                  id="billing-period-end"
                  type="date"
                  value={periodEnd}
                  onChange={(event) => setPeriodEnd(event.target.value)}
                />
                <Input
                  label="Total amount"
                  id="billing-total-amount"
                  type="number"
                  min="0"
                  step="0.01"
                  value={totalAmount}
                  onChange={(event) => setTotalAmount(event.target.value)}
                  placeholder="0.00"
                />
                <Input
                  label="Owner subsidy"
                  id="billing-owner-subsidy"
                  type="number"
                  min="0"
                  step="0.01"
                  value={ownerSubsidyAmount}
                  onChange={(event) => setOwnerSubsidyAmount(event.target.value)}
                  placeholder="0.00"
                />
                <div className="lg:col-span-2">
                  <label className="block text-sm font-medium text-gray-700" htmlFor="billing-notes">
                    Notes
                  </label>
                  <textarea
                    id="billing-notes"
                    className="mt-1 min-h-[96px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                    value={billNotes}
                    onChange={(event) => setBillNotes(event.target.value)}
                    placeholder="Notes for reviewers and tenants."
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={handleCreateBill} isLoading={createUtilityBill.isPending} className="w-full">
                    <Plus className="mr-2 h-4 w-4" />
                    Create bill draft
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-[1.02fr,0.98fr]">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Property utility bills</CardTitle>
                <CardDescription>
                  Draft and published bills for the selected property, with payable totals and publish status.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {billsQuery.isLoading ? (
                  <div className="space-y-3">
                    {[1, 2, 3].map((key) => (
                      <Skeleton key={key} className="h-16 w-full rounded-xl" />
                    ))}
                  </div>
                ) : billsQuery.error ? (
                  <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
                    {getErrorMessage(billsQuery.error, 'Unable to load utility bills for this property.')}
                  </div>
                ) : bills.length ? (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[760px]">
                      <thead>
                        <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                          <th className="pb-3 font-medium">Bill</th>
                          <th className="pb-3 font-medium">Period</th>
                          <th className="pb-3 font-medium">Payable</th>
                          <th className="pb-3 font-medium">Attachments</th>
                          <th className="pb-3 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {bills.map((bill) => (
                          <tr
                            key={bill.id}
                            className={`cursor-pointer border-b border-gray-100 last:border-0 ${
                              bill.id === selectedBillId ? 'bg-blue-50/70' : 'hover:bg-gray-50'
                            }`}
                            onClick={() => setSelectedBillId(bill.id)}
                          >
                            <td className="py-4">
                              <p className="font-medium text-gray-900">{formatUtilityBillType(bill.bill_type)}</p>
                              <p className="mt-1 text-xs text-gray-500">{bill.billing_period_label}</p>
                            </td>
                            <td className="py-4 text-sm text-gray-600">
                              {formatBillingWindow(bill.period_start, bill.period_end)}
                            </td>
                            <td className="py-4 text-sm font-medium text-gray-900">
                              {formatMoney(bill.payable_amount)}
                            </td>
                            <td className="py-4 text-sm text-gray-600">{bill.attachments.length}</td>
                            <td className="py-4">
                              <StatusBadge
                                label={formatInvoiceType(bill.status)}
                                tone={utilityBillStatusTone(bill.status)}
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyCard
                    title="No utility bills for this property"
                    description="Create a bill draft first, then upload evidence and configure tenant shares."
                    icon={Zap}
                  />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Bill detail and publish workflow</CardTitle>
                <CardDescription>
                  Preview attachments, configure bill shares, resolve disputes, and publish utility charges to tenants.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!selectedBill ? (
                  <EmptyCard
                    title="Select a utility bill"
                    description="Choose a property bill to upload attachments, configure splits, and publish tenant shares."
                    icon={Zap}
                  />
                ) : (
                  <div className="space-y-6">
                    <div className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-gray-200 bg-gray-50 p-4">
                      <div>
                        <div className="flex flex-wrap items-center gap-3">
                          <h3 className="text-lg font-semibold text-gray-900">
                            {formatUtilityBillType(selectedBill.bill_type)}
                          </h3>
                          <StatusBadge
                            label={formatInvoiceType(selectedBill.status)}
                            tone={utilityBillStatusTone(selectedBill.status)}
                          />
                        </div>
                        <p className="mt-2 text-sm text-gray-500">{selectedBill.billing_period_label}</p>
                        <p className="mt-1 text-sm text-gray-500">
                          Due {formatDateOnly(selectedBill.due_date)} · Created {formatDate(selectedBill.created_at)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">Payable amount</p>
                        <p className="mt-1 text-2xl font-semibold text-gray-900">
                          {formatMoney(selectedBill.payable_amount)}
                        </p>
                        <p className="mt-1 text-sm text-gray-500">
                          Owner subsidy {formatMoney(selectedBill.owner_subsidy_amount)}
                        </p>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-gray-200 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">Upload utility evidence</p>
                          <p className="mt-1 text-sm text-gray-500">
                            Attach PDFs or images so tenants can review the source bill before they pay.
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <input
                            key={attachmentInputKey}
                            type="file"
                            onChange={(event) => setAttachmentFile(event.target.files?.[0] ?? null)}
                            className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                          />
                          <Button
                            variant="outline"
                            onClick={handleAttachmentUpload}
                            isLoading={uploadAttachment.isPending}
                            disabled={!attachmentFile}
                          >
                            <Upload className="mr-2 h-4 w-4" />
                            Upload
                          </Button>
                        </div>
                      </div>

                      <div className="mt-4">
                        <AttachmentPreviewList attachments={selectedBill.attachments} />
                      </div>
                    </div>

                    <div className="rounded-2xl border border-gray-200 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">Split editor</p>
                          <p className="mt-1 text-sm text-gray-500">
                            Auto-split evenly or manually tune each tenant’s share for this billing period.
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          <Button
                            variant="outline"
                            onClick={() => handleAutoSplit('equal')}
                            isLoading={configureSplits.isPending}
                            disabled={selectedBill.published_at !== null}
                          >
                            Equal split
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleAutoSplit('single')}
                            isLoading={configureSplits.isPending}
                            disabled={selectedBill.published_at !== null || propertyTenantCount !== 1}
                          >
                            Single split
                          </Button>
                        </div>
                      </div>

                      {splitError ? (
                        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                          {splitError}
                        </div>
                      ) : null}

                      <div className="mt-4 overflow-x-auto">
                        <table className="w-full min-w-[880px]">
                          <thead>
                            <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                              <th className="pb-3 font-medium">Include</th>
                              <th className="pb-3 font-medium">Tenant</th>
                              <th className="pb-3 font-medium">Bookings</th>
                              <th className="pb-3 font-medium">Method</th>
                              <th className="pb-3 font-medium">Percent</th>
                              <th className="pb-3 font-medium">Fixed amount</th>
                            </tr>
                          </thead>
                          <tbody>
                            {splitRows.length ? (
                              splitRows.map((row) => (
                                <tr key={row.tenantUserId} className="border-b border-gray-100 last:border-0">
                                  <td className="py-4">
                                    <input
                                      type="checkbox"
                                      checked={row.enabled}
                                      onChange={(event) =>
                                        setSplitRows((current) =>
                                          current.map((item) =>
                                            item.tenantUserId === row.tenantUserId
                                              ? { ...item, enabled: event.target.checked }
                                              : item,
                                          ),
                                        )
                                      }
                                    />
                                  </td>
                                  <td className="py-4 text-sm font-medium text-gray-900">{row.tenantUserId}</td>
                                  <td className="py-4 text-sm text-gray-600">
                                    {row.bookingNumbers.length ? row.bookingNumbers.join(', ') : 'No overlapping booking'}
                                  </td>
                                  <td className="py-4">
                                    <select
                                      className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                                      value={row.splitMethod}
                                      onChange={(event) =>
                                        setSplitRows((current) =>
                                          current.map((item) =>
                                            item.tenantUserId === row.tenantUserId
                                              ? {
                                                  ...item,
                                                  splitMethod: event.target.value as UtilityBillSplitMethod,
                                                }
                                              : item,
                                          ),
                                        )
                                      }
                                      disabled={!row.enabled}
                                    >
                                      {['equal', 'percentage', 'fixed', 'single'].map((method) => (
                                        <option key={method} value={method}>
                                          {formatSplitMethod(method)}
                                        </option>
                                      ))}
                                    </select>
                                  </td>
                                  <td className="py-4">
                                    <Input
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      value={row.splitPercent}
                                      onChange={(event) =>
                                        setSplitRows((current) =>
                                          current.map((item) =>
                                            item.tenantUserId === row.tenantUserId
                                              ? { ...item, splitPercent: event.target.value }
                                              : item,
                                          ),
                                        )
                                      }
                                      disabled={!row.enabled || row.splitMethod !== 'percentage'}
                                      placeholder="%"
                                    />
                                  </td>
                                  <td className="py-4">
                                    <Input
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      value={row.assignedAmount}
                                      onChange={(event) =>
                                        setSplitRows((current) =>
                                          current.map((item) =>
                                            item.tenantUserId === row.tenantUserId
                                              ? { ...item, assignedAmount: event.target.value }
                                              : item,
                                          ),
                                        )
                                      }
                                      disabled={!row.enabled || row.splitMethod !== 'fixed'}
                                      placeholder="NPR"
                                    />
                                  </td>
                                </tr>
                              ))
                            ) : (
                              <tr>
                                <td colSpan={6} className="py-6 text-center text-sm text-gray-500">
                                  No overlapping tenant bookings were found for this billing period yet.
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>

                      <div className="mt-4 flex justify-end">
                        <Button
                          onClick={handleSaveManualSplits}
                          isLoading={configureSplits.isPending}
                          disabled={selectedBill.published_at !== null || !splitRows.length}
                        >
                          Save split configuration
                        </Button>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-gray-200 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">Current shares</p>
                          <p className="mt-1 text-sm text-gray-500">
                            Review calculated amounts, invoice linkage, and dispute state before publishing.
                          </p>
                        </div>
                        <Button
                          onClick={() => setPublishDialogOpen(true)}
                          disabled={!selectedBill.splits.length || selectedBill.published_at !== null}
                        >
                          <Send className="mr-2 h-4 w-4" />
                          Publish bill
                        </Button>
                      </div>

                      <div className="mt-4 space-y-3">
                        {selectedBill.splits.length ? (
                          selectedBill.splits.map((split) => (
                            <div key={split.id} className="rounded-2xl border border-gray-200 p-4">
                              <div className="flex flex-wrap items-start justify-between gap-3">
                                <div>
                                  <p className="font-medium text-gray-900">{split.tenant_user_id}</p>
                                  <p className="mt-1 text-sm text-gray-500">
                                    {formatSplitMethod(split.split_method)}
                                    {split.invoice_id ? ` · Invoice ${split.invoice_id}` : ''}
                                  </p>
                                  <p className="mt-1 text-sm text-gray-500">
                                    Due {formatDate(split.due_at)}
                                  </p>
                                </div>
                                <div className="text-right">
                                  <p className="text-sm font-semibold text-gray-900">
                                    {formatMoney(split.assigned_amount)}
                                  </p>
                                  <p className="mt-1 text-sm text-gray-500">
                                    Outstanding {formatMoney(split.outstanding_amount)}
                                  </p>
                                  <div className="mt-2">
                                    <StatusBadge
                                      label={formatInvoiceType(split.status)}
                                      tone={splitStatusTone(split.status)}
                                    />
                                  </div>
                                </div>
                              </div>

                              {split.status === 'disputed' ? (
                                <div className="mt-4 border-t border-gray-200 pt-4">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() =>
                                      setActiveSplitResolveId((current) =>
                                        current === split.id ? null : split.id,
                                      )
                                    }
                                  >
                                    <Scale className="mr-2 h-4 w-4" />
                                    {activeSplitResolveId === split.id ? 'Cancel resolution' : 'Resolve dispute'}
                                  </Button>
                                  {activeSplitResolveId === split.id ? (
                                    <div className="mt-4 space-y-3">
                                      <select
                                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                                        value={splitResolutionOutcome}
                                        onChange={(event) =>
                                          setSplitResolutionOutcome(
                                            event.target.value as UtilityBillDisputeStatus,
                                          )
                                        }
                                      >
                                        {['resolved', 'rejected', 'waived'].map((outcome) => (
                                          <option key={outcome} value={outcome}>
                                            {formatInvoiceType(outcome)}
                                          </option>
                                        ))}
                                      </select>
                                      <textarea
                                        className="min-h-[96px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                                        value={splitResolutionNotes}
                                        onChange={(event) => setSplitResolutionNotes(event.target.value)}
                                        placeholder="Explain the outcome for this disputed bill share."
                                      />
                                      <Button
                                        onClick={handleResolveSplitDispute}
                                        isLoading={resolveBillShareDispute.isPending}
                                      >
                                        Save dispute decision
                                      </Button>
                                    </div>
                                  ) : null}
                                </div>
                              ) : null}
                            </div>
                          ))
                        ) : (
                          <p className="text-sm text-gray-500">
                            No bill-share rows have been configured yet.
                          </p>
                        )}
                      </div>
                    </div>

                    {disputedSplits.length ? (
                      <div className="rounded-2xl border border-red-200 bg-red-50 p-4">
                        <div className="flex items-center gap-2 text-sm font-semibold text-red-800">
                          <AlertTriangle className="h-4 w-4" />
                          Open utility disputes
                        </div>
                        <p className="mt-2 text-sm text-red-700">
                          {disputedSplits.length} tenant share{disputedSplits.length > 1 ? 's are' : ' is'} awaiting resolution.
                        </p>
                      </div>
                    ) : null}

                    <div className="rounded-2xl border border-gray-200 p-4">
                      <p className="text-sm font-semibold text-gray-900">Bill history</p>
                      <div className="mt-4">
                        {billHistoryQuery.isLoading ? (
                          <div className="space-y-3">
                            {[1, 2].map((key) => (
                              <Skeleton key={key} className="h-16 w-full rounded-xl" />
                            ))}
                          </div>
                        ) : billHistoryQuery.error ? (
                          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
                            {getErrorMessage(billHistoryQuery.error, 'Unable to load bill history.')}
                          </div>
                        ) : (
                          <ActivityTimeline
                            entries={billHistoryQuery.data?.entries ?? []}
                            emptyState="No bill history has been recorded yet."
                          />
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-xl">Booking closeout workspace</CardTitle>
                <CardDescription>
                  Review the rent ledger for a property booking, add additional charges, and resolve disputed checkout items.
                </CardDescription>
              </div>
              {propertyBookings.length ? (
                <select
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                  value={selectedBookingId}
                  onChange={(event) => setSelectedBookingId(event.target.value)}
                >
                  {propertyBookings.map((booking) => (
                    <option key={booking.id} value={booking.id}>
                      {booking.booking_number} · {booking.property.name}
                    </option>
                  ))}
                </select>
              ) : null}
            </CardHeader>
            <CardContent>
              {!propertyBookings.length ? (
                <EmptyCard
                  title="No active booking ledger"
                  description="Once a booking overlaps this property, it will appear here for checkout charge management."
                  icon={FileClock}
                />
              ) : ledgerQuery.isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((key) => (
                    <Skeleton key={key} className="h-16 w-full rounded-xl" />
                  ))}
                </div>
              ) : ledgerQuery.error ? (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-700">
                  {getErrorMessage(ledgerQuery.error, 'Unable to load the selected booking ledger.')}
                </div>
              ) : ledgerQuery.data ? (
                <div className="space-y-6">
                  <div className="grid gap-4 lg:grid-cols-[1fr,1fr]">
                    <div className="rounded-2xl border border-gray-200 p-4">
                      <p className="text-sm font-semibold text-gray-900">Create additional charge</p>
                      <div className="mt-4 grid gap-3 sm:grid-cols-2">
                        <div className="space-y-2">
                          <label className="text-sm font-medium text-gray-700" htmlFor="charge-type">
                            Charge type
                          </label>
                          <select
                            id="charge-type"
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                            value={chargeType}
                            onChange={(event) => setChargeType(event.target.value)}
                          >
                            {['damage', 'cleaning', 'late_checkout', 'other'].map((type) => (
                              <option key={type} value={type}>
                                {formatInvoiceType(type)}
                              </option>
                            ))}
                          </select>
                        </div>
                        <Input
                          label="Amount"
                          id="charge-amount"
                          type="number"
                          min="0"
                          step="0.01"
                          value={chargeAmount}
                          onChange={(event) => setChargeAmount(event.target.value)}
                          placeholder="0.00"
                        />
                        <div className="sm:col-span-2">
                          <Input
                            label="Description"
                            id="charge-description"
                            value={chargeDescription}
                            onChange={(event) => setChargeDescription(event.target.value)}
                            placeholder="Describe the post-tenancy charge"
                          />
                        </div>
                        <div className="sm:col-span-2">
                          <Input
                            label="Evidence URL"
                            id="charge-evidence"
                            value={chargeEvidenceUrl}
                            onChange={(event) => setChargeEvidenceUrl(event.target.value)}
                            placeholder="Optional evidence link"
                          />
                        </div>
                      </div>
                      <Button
                        className="mt-4"
                        onClick={handleCreateAdditionalCharge}
                        isLoading={createAdditionalCharge.isPending}
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        Add charge
                      </Button>
                    </div>

                    <div className="rounded-2xl border border-gray-200 p-4">
                      <p className="text-sm font-semibold text-gray-900">Ledger summary</p>
                      <div className="mt-4 grid gap-3 sm:grid-cols-3">
                        <div className="rounded-2xl border border-gray-200 px-4 py-3">
                          <p className="text-xs uppercase tracking-[0.16em] text-gray-400">Total</p>
                          <p className="mt-1 text-sm font-semibold text-gray-900">
                            {formatMoney(ledgerQuery.data.total_amount, ledgerQuery.data.currency)}
                          </p>
                        </div>
                        <div className="rounded-2xl border border-gray-200 px-4 py-3">
                          <p className="text-xs uppercase tracking-[0.16em] text-gray-400">Paid</p>
                          <p className="mt-1 text-sm font-semibold text-gray-900">
                            {formatMoney(ledgerQuery.data.paid_amount, ledgerQuery.data.currency)}
                          </p>
                        </div>
                        <div className="rounded-2xl border border-gray-200 px-4 py-3">
                          <p className="text-xs uppercase tracking-[0.16em] text-gray-400">Outstanding</p>
                          <p className="mt-1 text-sm font-semibold text-gray-900">
                            {formatMoney(ledgerQuery.data.outstanding_amount, ledgerQuery.data.currency)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {selectedChargeList.length ? (
                      selectedChargeList.map((charge) => (
                        <div key={charge.id} className="rounded-2xl border border-gray-200 p-4">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <div className="flex flex-wrap items-center gap-3">
                                <p className="font-medium text-gray-900">{charge.description}</p>
                                <StatusBadge
                                  label={formatInvoiceType(charge.status)}
                                  tone={additionalChargeStatusTone(charge.status)}
                                />
                              </div>
                              <p className="mt-2 text-sm text-gray-500">
                                {formatInvoiceType(charge.charge_type)} · Raised {formatDate(charge.created_at)}
                              </p>
                              {charge.dispute_reason ? (
                                <p className="mt-1 text-sm text-gray-600">Dispute: {charge.dispute_reason}</p>
                              ) : null}
                              {charge.resolution_notes ? (
                                <p className="mt-1 text-sm text-gray-600">
                                  Resolution: {charge.resolution_notes}
                                </p>
                              ) : null}
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-semibold text-gray-900">
                                {formatMoney(charge.amount, ledgerQuery.data.currency)}
                              </p>
                              {charge.status === 'disputed' ? (
                                <Button
                                  className="mt-3"
                                  variant="outline"
                                  size="sm"
                                  onClick={() =>
                                    setActiveChargeResolveId((current) =>
                                      current === charge.id ? null : charge.id,
                                    )
                                  }
                                >
                                  <Scale className="mr-2 h-4 w-4" />
                                  {activeChargeResolveId === charge.id ? 'Cancel resolution' : 'Resolve dispute'}
                                </Button>
                              ) : null}
                            </div>
                          </div>

                          {activeChargeResolveId === charge.id ? (
                            <div className="mt-4 space-y-3 border-t border-gray-200 pt-4">
                              <select
                                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                                value={chargeResolutionOutcome}
                                onChange={(event) =>
                                  setChargeResolutionOutcome(event.target.value as AdditionalChargeRecord['status'])
                                }
                              >
                                {['accepted', 'partially_accepted', 'waived'].map((outcome) => (
                                  <option key={outcome} value={outcome}>
                                    {formatInvoiceType(outcome)}
                                  </option>
                                ))}
                              </select>
                              <Input
                                type="number"
                                min="0"
                                step="0.01"
                                value={chargeResolvedAmount}
                                onChange={(event) => setChargeResolvedAmount(event.target.value)}
                                placeholder="Resolved amount (optional)"
                              />
                              <textarea
                                className="min-h-[96px] w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900"
                                value={chargeResolutionNotes}
                                onChange={(event) => setChargeResolutionNotes(event.target.value)}
                                placeholder="Document how the dispute was resolved."
                              />
                              <Button
                                onClick={handleResolveCharge}
                                isLoading={resolveAdditionalCharge.isPending}
                              >
                                Save resolution
                              </Button>
                            </div>
                          ) : null}
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">No additional charges have been created for this booking.</p>
                    )}
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <div className="grid gap-6 xl:grid-cols-[1fr,1fr]">
            <InvoiceListCard
              title="Invoice visibility"
              description="Review invoice state across rent schedules and published utility bill shares."
              invoices={managementInvoices}
              selectedInvoiceId={selectedInvoiceId}
              onSelect={setSelectedInvoiceId}
              isLoading={invoicesQuery.isLoading}
              error={invoicesQuery.error}
            />
            <InvoiceDetailCard
              title="Invoice inspection"
              invoice={selectedInvoice}
              isLoading={invoiceDetailQuery.isLoading}
              error={invoiceDetailQuery.error}
              paymentProviders={[]}
              paymentProvider={FALLBACK_PROVIDER}
              onDownloadReceipt={handleReceiptDownload}
              isDownloadingReceipt={downloadReceipt.isPending}
            />
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="pt-6">
            <EmptyCard
              title="Choose a property to manage bills"
              description="Management workflows stay on the website so owners and admins can work through evidence, splits, and publish state in one place."
              icon={Building2}
            />
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={publishDialogOpen}
        title="Publish utility bill to tenants?"
        description="Publishing creates tenant-payable bill share invoices and exposes this bill in tenant billing history."
        confirmLabel="Publish bill"
        onCancel={() => setPublishDialogOpen(false)}
        onConfirm={handlePublishBill}
        isLoading={publishUtilityBill.isPending}
      />
    </div>
  );
}

export function BillingWorkspace() {
  const user = useAuthStore((state) => state.user);
  const paymentProvidersQuery = usePaymentProviders();

  const canUseTenantBilling = hasTenantBillingAccess(user?.roles, user?.is_superuser);
  const canManageBilling = hasBillingManagementAccess(user?.roles, user?.is_superuser);
  const availableModes = useMemo(
    () => [
      ...(canUseTenantBilling ? (['tenant'] as WorkspaceMode[]) : []),
      ...(canManageBilling ? (['management'] as WorkspaceMode[]) : []),
    ],
    [canManageBilling, canUseTenantBilling],
  );

  const [activeMode, setActiveMode] = useState<WorkspaceMode>(
    canManageBilling ? 'management' : 'tenant',
  );

  useEffect(() => {
    if (!availableModes.length) {
      return;
    }

    if (!availableModes.includes(activeMode)) {
      setActiveMode(availableModes[0]);
    }
  }, [activeMode, availableModes]);

  const paymentProviders = paymentProvidersQuery.data?.length
    ? paymentProvidersQuery.data
    : [FALLBACK_PROVIDER];

  if (!availableModes.length) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 px-6 py-5 text-sm text-amber-700">
        This account does not currently expose billing workflows on the website.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Billing workspace</h1>
          <p className="text-gray-500">
            Tenant checkout and invoice actions stay available here, while owner and admin utility-bill workflows remain web-first.
          </p>
        </div>
        {availableModes.length > 1 ? (
          <div className="flex items-center gap-2 rounded-2xl border border-gray-200 bg-white p-1">
            <Button
              variant={activeMode === 'tenant' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveMode('tenant')}
            >
              <Wallet className="mr-2 h-4 w-4" />
              Tenant billing
            </Button>
            <Button
              variant={activeMode === 'management' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setActiveMode('management')}
            >
              <Building2 className="mr-2 h-4 w-4" />
              Utility management
            </Button>
          </div>
        ) : null}
      </div>

      {paymentProvidersQuery.error ? (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          {getErrorMessage(
            paymentProvidersQuery.error,
            'Hosted payment provider metadata is temporarily unavailable, so the workspace is using a safe default provider.',
          )}
        </div>
      ) : null}

      {activeMode === 'management' ? (
        <ManagementBillingView />
      ) : (
        <TenantBillingView paymentProviders={paymentProviders} />
      )}
    </div>
  );
}
