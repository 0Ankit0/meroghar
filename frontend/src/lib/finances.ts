import { unwrapApiData } from './properties';
import type {
  AdditionalChargeRecord,
  InvoiceLineItem,
  InvoiceListParams,
  InvoiceListResponse,
  InvoicePaymentRecord,
  InvoiceRecord,
  InvoiceReminder,
  RentLedger,
  RentLedgerEntry,
  UtilityBillAttachment,
  UtilityBillDispute,
  UtilityBillHistory,
  UtilityBillHistoryEntry,
  UtilityBillListResponse,
  UtilityBillRecord,
  UtilityBillShareListResponse,
  UtilityBillShareRecord,
  UtilityBillSplit,
} from '@/types';

type UnknownRecord = Record<string, unknown>;

interface ApiEnvelope<T> {
  success?: boolean;
  data?: T;
  meta?: UnknownRecord;
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isApiEnvelope<T>(value: unknown): value is ApiEnvelope<T> {
  if (!isRecord(value)) {
    return false;
  }

  return 'data' in value && ('success' in value || 'meta' in value);
}

function getArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function toOptionalString(value: unknown): string | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  return String(value);
}

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === '') {
    return null;
  }

  const parsed = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function humanize(value: string): string {
  return value
    .replace(/[._-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function normalizeRoles(roles?: string[] | null): string[] {
  return (roles ?? [])
    .map((role) => role.trim().toLowerCase())
    .filter(Boolean);
}

function hasRoleFragment(roles: string[], fragments: readonly string[]): boolean {
  return roles.some((role) => fragments.some((fragment) => role.includes(fragment)));
}

export function buildInvoiceApiParams(params?: InvoiceListParams): Record<string, string | number> {
  if (!params) {
    return {};
  }

  const requestParams: Record<string, string | number> = {};
  if (params.page) {
    requestParams.page = params.page;
  }
  if (params.per_page) {
    requestParams.per_page = params.per_page;
  }
  if (params.status && params.status !== 'all') {
    requestParams.status = params.status;
  }
  return requestParams;
}

function unwrapBillingPayload<T>(payload: T | ApiEnvelope<T>): T {
  if (isApiEnvelope<T>(payload)) {
    return payload.data as T;
  }

  return unwrapApiData(payload);
}

export function normalizeInvoiceLineItem(payload: unknown): InvoiceLineItem {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? ''),
    invoice_id: String(record.invoice_id ?? record.invoiceId ?? ''),
    line_item_type: String(record.line_item_type ?? record.lineItemType ?? 'rent'),
    description: String(record.description ?? ''),
    amount: toNumber(record.amount) ?? 0,
    tax_rate: toNumber(record.tax_rate ?? record.taxRate) ?? 0,
    tax_amount: toNumber(record.tax_amount ?? record.taxAmount) ?? 0,
    metadata_json: isRecord(record.metadata_json ?? record.metadataJson)
      ? ((record.metadata_json ?? record.metadataJson) as Record<string, unknown>)
      : null,
  };
}

export function normalizeInvoiceReminder(payload: unknown): InvoiceReminder {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? ''),
    invoice_id: String(record.invoice_id ?? record.invoiceId ?? ''),
    reminder_type: String(record.reminder_type ?? record.reminderType ?? 't_minus_3'),
    scheduled_for: toOptionalString(record.scheduled_for ?? record.scheduledFor) ?? '',
    sent_at: toOptionalString(record.sent_at ?? record.sentAt),
    status: String(record.status ?? 'scheduled'),
    channel_status_json: isRecord(record.channel_status_json ?? record.channelStatusJson)
      ? ((record.channel_status_json ?? record.channelStatusJson) as Record<string, unknown>)
      : null,
  };
}

export function normalizeInvoicePaymentRecord(payload: unknown): InvoicePaymentRecord {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? ''),
    reference_type: String(record.reference_type ?? record.referenceType ?? 'invoice'),
    reference_id: String(record.reference_id ?? record.referenceId ?? ''),
    payer_user_id: String(record.payer_user_id ?? record.payerUserId ?? ''),
    payment_method: String(record.payment_method ?? record.paymentMethod ?? 'khalti'),
    status: String(record.status ?? 'pending'),
    amount: toNumber(record.amount) ?? 0,
    currency: toOptionalString(record.currency) ?? 'NPR',
    gateway_ref: toOptionalString(record.gateway_ref ?? record.gatewayRef) ?? '',
    gateway_response_json: isRecord(record.gateway_response_json ?? record.gatewayResponseJson)
      ? ((record.gateway_response_json ?? record.gatewayResponseJson) as Record<string, unknown>)
      : null,
    is_offline: Boolean(record.is_offline ?? record.isOffline),
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? '',
    confirmed_at: toOptionalString(record.confirmed_at ?? record.confirmedAt),
  };
}

export function normalizeInvoice(payload: unknown): InvoiceRecord {
  const data = unwrapBillingPayload(payload);
  const record = isRecord(data) ? data : {};

  return {
    id: String(record.id ?? ''),
    invoice_number: String(record.invoice_number ?? record.invoiceNumber ?? 'Invoice'),
    booking_id: toOptionalString(record.booking_id ?? record.bookingId),
    tenant_user_id: String(record.tenant_user_id ?? record.tenantUserId ?? ''),
    owner_user_id: String(record.owner_user_id ?? record.ownerUserId ?? ''),
    invoice_type: String(record.invoice_type ?? record.invoiceType ?? 'rent'),
    currency: toOptionalString(record.currency) ?? 'NPR',
    subtotal: toNumber(record.subtotal) ?? 0,
    tax_amount: toNumber(record.tax_amount ?? record.taxAmount) ?? 0,
    total_amount: toNumber(record.total_amount ?? record.totalAmount) ?? 0,
    paid_amount: toNumber(record.paid_amount ?? record.paidAmount) ?? 0,
    outstanding_amount: toNumber(record.outstanding_amount ?? record.outstandingAmount) ?? 0,
    status: String(record.status ?? 'draft'),
    due_date: toOptionalString(record.due_date ?? record.dueDate) ?? '',
    period_start: toOptionalString(record.period_start ?? record.periodStart),
    period_end: toOptionalString(record.period_end ?? record.periodEnd),
    metadata_json: isRecord(record.metadata_json ?? record.metadataJson)
      ? ((record.metadata_json ?? record.metadataJson) as Record<string, unknown>)
      : null,
    line_items: getArray(record.line_items ?? record.lineItems).map(normalizeInvoiceLineItem),
    reminders: getArray(record.reminders).map(normalizeInvoiceReminder),
    payments: getArray(record.payments).map(normalizeInvoicePaymentRecord),
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? '',
    paid_at: toOptionalString(record.paid_at ?? record.paidAt),
  };
}

export function normalizeInvoiceListResponse(payload: unknown): InvoiceListResponse {
  const data = unwrapBillingPayload(payload);

  if (Array.isArray(data)) {
    return {
      items: data.map(normalizeInvoice),
      total: data.length,
      page: 1,
      per_page: data.length || 20,
      has_more: false,
    };
  }

  const record = isRecord(data) ? data : {};
  const root = isRecord(payload) ? payload : {};
  const meta = isRecord(root.meta) ? root.meta : {};
  const items = getArray(record.items ?? record.invoices ?? record.results ?? []).map(normalizeInvoice);
  const total = toNumber(record.total ?? record.count ?? meta.total ?? meta.count) ?? items.length;
  const page =
    toNumber(record.page ?? record.current_page ?? record.currentPage ?? meta.page ?? meta.current_page) ??
    1;
  const perPage =
    toNumber(record.per_page ?? record.perPage ?? record.limit ?? meta.per_page ?? meta.perPage) ??
    (items.length || 20);
  const hasMore = Boolean(record.has_more ?? record.hasMore ?? page * perPage < total);

  return {
    items,
    total,
    page,
    per_page: perPage,
    has_more: hasMore,
  };
}

export function normalizeAdditionalCharge(payload: unknown): AdditionalChargeRecord {
  const data = unwrapBillingPayload(payload);
  const record = isRecord(data) ? data : {};

  return {
    id: String(record.id ?? ''),
    booking_id: String(record.booking_id ?? record.bookingId ?? ''),
    invoice_id: toOptionalString(record.invoice_id ?? record.invoiceId),
    charge_type: String(record.charge_type ?? record.chargeType ?? 'damage'),
    description: String(record.description ?? ''),
    amount: toNumber(record.amount) ?? 0,
    resolved_amount: toNumber(record.resolved_amount ?? record.resolvedAmount),
    evidence_url: toOptionalString(record.evidence_url ?? record.evidenceUrl) ?? '',
    status: String(record.status ?? 'raised'),
    dispute_reason: toOptionalString(record.dispute_reason ?? record.disputeReason) ?? '',
    resolution_notes: toOptionalString(record.resolution_notes ?? record.resolutionNotes) ?? '',
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? '',
    resolved_at: toOptionalString(record.resolved_at ?? record.resolvedAt),
  };
}

export function normalizeRentLedgerEntry(payload: unknown): RentLedgerEntry {
  const record = isRecord(payload) ? payload : {};

  return {
    period_start: toOptionalString(record.period_start ?? record.periodStart) ?? '',
    period_end: toOptionalString(record.period_end ?? record.periodEnd) ?? '',
    amount_due: toNumber(record.amount_due ?? record.amountDue) ?? 0,
    invoice_id: toOptionalString(record.invoice_id ?? record.invoiceId),
    invoice_status: toOptionalString(record.invoice_status ?? record.invoiceStatus),
    due_date: toOptionalString(record.due_date ?? record.dueDate),
    paid_amount: toNumber(record.paid_amount ?? record.paidAmount) ?? 0,
    outstanding_amount: toNumber(record.outstanding_amount ?? record.outstandingAmount) ?? 0,
  };
}

export function normalizeRentLedger(payload: unknown): RentLedger {
  const data = unwrapBillingPayload(payload);
  const record = isRecord(data) ? data : {};

  return {
    booking_id: String(record.booking_id ?? record.bookingId ?? ''),
    currency: toOptionalString(record.currency) ?? 'NPR',
    entries: getArray(record.entries).map(normalizeRentLedgerEntry),
    additional_charges: getArray(record.additional_charges ?? record.additionalCharges).map(
      normalizeAdditionalCharge
    ),
    total_amount: toNumber(record.total_amount ?? record.totalAmount) ?? 0,
    paid_amount: toNumber(record.paid_amount ?? record.paidAmount) ?? 0,
    outstanding_amount: toNumber(record.outstanding_amount ?? record.outstandingAmount) ?? 0,
  };
}

export function normalizeUtilityBillAttachment(payload: unknown): UtilityBillAttachment {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? ''),
    utility_bill_id: String(record.utility_bill_id ?? record.utilityBillId ?? ''),
    file_url: toOptionalString(record.file_url ?? record.fileUrl) ?? '',
    file_type: toOptionalString(record.file_type ?? record.fileType) ?? 'application/octet-stream',
    checksum: toOptionalString(record.checksum) ?? '',
    uploaded_at: toOptionalString(record.uploaded_at ?? record.uploadedAt) ?? '',
  };
}

export function normalizeUtilityBillSplit(payload: unknown): UtilityBillSplit {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? ''),
    utility_bill_id: String(record.utility_bill_id ?? record.utilityBillId ?? ''),
    tenant_user_id: String(record.tenant_user_id ?? record.tenantUserId ?? ''),
    invoice_id: toOptionalString(record.invoice_id ?? record.invoiceId),
    split_method: String(record.split_method ?? record.splitMethod ?? 'equal'),
    split_percent: toNumber(record.split_percent ?? record.splitPercent),
    assigned_amount: toNumber(record.assigned_amount ?? record.assignedAmount) ?? 0,
    paid_amount: toNumber(record.paid_amount ?? record.paidAmount) ?? 0,
    outstanding_amount: toNumber(record.outstanding_amount ?? record.outstandingAmount) ?? 0,
    status: String(record.status ?? 'pending'),
    due_at: toOptionalString(record.due_at ?? record.dueAt),
    paid_at: toOptionalString(record.paid_at ?? record.paidAt),
  };
}

export function normalizeUtilityBillDispute(payload: unknown): UtilityBillDispute {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? ''),
    utility_bill_split_id: String(record.utility_bill_split_id ?? record.utilityBillSplitId ?? ''),
    opened_by_user_id: String(record.opened_by_user_id ?? record.openedByUserId ?? ''),
    status: String(record.status ?? 'open'),
    reason: toOptionalString(record.reason) ?? '',
    resolution_notes: toOptionalString(record.resolution_notes ?? record.resolutionNotes) ?? '',
    opened_at: toOptionalString(record.opened_at ?? record.openedAt) ?? '',
    resolved_at: toOptionalString(record.resolved_at ?? record.resolvedAt),
  };
}

export function normalizeUtilityBill(payload: unknown): UtilityBillRecord {
  const data = unwrapBillingPayload(payload);
  const record = isRecord(data) ? data : {};

  return {
    id: String(record.id ?? ''),
    property_id: String(record.property_id ?? record.propertyId ?? ''),
    created_by_user_id: String(record.created_by_user_id ?? record.createdByUserId ?? ''),
    bill_type: String(record.bill_type ?? record.billType ?? 'electricity'),
    billing_period_label: String(record.billing_period_label ?? record.billingPeriodLabel ?? 'Billing period'),
    period_start: toOptionalString(record.period_start ?? record.periodStart) ?? '',
    period_end: toOptionalString(record.period_end ?? record.periodEnd) ?? '',
    due_date: toOptionalString(record.due_date ?? record.dueDate) ?? '',
    total_amount: toNumber(record.total_amount ?? record.totalAmount) ?? 0,
    owner_subsidy_amount: toNumber(record.owner_subsidy_amount ?? record.ownerSubsidyAmount) ?? 0,
    payable_amount: toNumber(record.payable_amount ?? record.payableAmount) ?? 0,
    status: String(record.status ?? 'draft'),
    notes: toOptionalString(record.notes) ?? '',
    attachments: getArray(record.attachments).map(normalizeUtilityBillAttachment),
    splits: getArray(record.splits).map(normalizeUtilityBillSplit),
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? '',
    published_at: toOptionalString(record.published_at ?? record.publishedAt),
  };
}

export function normalizeUtilityBillListResponse(payload: unknown): UtilityBillListResponse {
  const data = unwrapBillingPayload(payload);

  if (Array.isArray(data)) {
    return {
      items: data.map(normalizeUtilityBill),
      total: data.length,
      page: 1,
      per_page: data.length || 20,
      has_more: false,
    };
  }

  const record = isRecord(data) ? data : {};
  const root = isRecord(payload) ? payload : {};
  const meta = isRecord(root.meta) ? root.meta : {};
  const items = getArray(record.items ?? record.bills ?? record.results ?? []).map(normalizeUtilityBill);
  const total = toNumber(record.total ?? record.count ?? meta.total ?? meta.count) ?? items.length;
  const page =
    toNumber(record.page ?? record.current_page ?? record.currentPage ?? meta.page ?? meta.current_page) ??
    1;
  const perPage =
    toNumber(record.per_page ?? record.perPage ?? record.limit ?? meta.per_page ?? meta.perPage) ??
    (items.length || 20);
  const hasMore = Boolean(record.has_more ?? record.hasMore ?? page * perPage < total);

  return {
    items,
    total,
    page,
    per_page: perPage,
    has_more: hasMore,
  };
}

export function normalizeUtilityBillShare(payload: unknown): UtilityBillShareRecord {
  const data = unwrapBillingPayload(payload);
  const record = isRecord(data) ? data : {};

  return {
    split: normalizeUtilityBillSplit(record.split),
    bill: normalizeUtilityBill(record.bill),
    disputes: getArray(record.disputes).map(normalizeUtilityBillDispute),
  };
}

export function normalizeUtilityBillShareListResponse(payload: unknown): UtilityBillShareListResponse {
  const data = unwrapBillingPayload(payload);

  if (Array.isArray(data)) {
    return {
      items: data.map(normalizeUtilityBillShare),
      total: data.length,
    };
  }

  const record = isRecord(data) ? data : {};
  const items = getArray(record.items ?? record.bill_shares ?? record.billShares ?? []).map(
    normalizeUtilityBillShare
  );

  return {
    items,
    total: toNumber(record.total ?? record.count) ?? items.length,
  };
}

export function normalizeUtilityBillHistoryEntry(payload: unknown): UtilityBillHistoryEntry {
  const record = isRecord(payload) ? payload : {};

  return {
    event_type: String(record.event_type ?? record.eventType ?? 'utility_bill.updated'),
    message: toOptionalString(record.message) ?? 'Billing event recorded.',
    occurred_at: toOptionalString(record.occurred_at ?? record.occurredAt) ?? '',
    metadata_json: isRecord(record.metadata_json ?? record.metadataJson)
      ? ((record.metadata_json ?? record.metadataJson) as Record<string, unknown>)
      : null,
  };
}

export function normalizeUtilityBillHistory(payload: unknown): UtilityBillHistory {
  const data = unwrapBillingPayload(payload);
  const record = isRecord(data) ? data : {};

  return {
    bill_id: String(record.bill_id ?? record.billId ?? ''),
    entries: getArray(record.entries).map(normalizeUtilityBillHistoryEntry),
  };
}

export function formatInvoiceType(type?: string | null): string {
  if (!type) {
    return 'Invoice';
  }

  return humanize(type);
}

export function formatUtilityBillType(type?: string | null): string {
  if (!type) {
    return 'Utility bill';
  }

  return humanize(type);
}

export function formatSplitMethod(method?: string | null): string {
  if (!method) {
    return 'Split';
  }

  return humanize(method);
}

export function invoiceStatusTone(status?: string | null): string {
  switch ((status ?? '').toLowerCase()) {
    case 'paid':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'partially_paid':
      return 'border-blue-200 bg-blue-50 text-blue-700';
    case 'overdue':
      return 'border-red-200 bg-red-50 text-red-700';
    case 'sent':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    case 'waived':
      return 'border-slate-200 bg-slate-100 text-slate-700';
    case 'draft':
    default:
      return 'border-slate-200 bg-slate-50 text-slate-700';
  }
}

export function utilityBillStatusTone(status?: string | null): string {
  switch ((status ?? '').toLowerCase()) {
    case 'settled':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'partially_paid':
      return 'border-blue-200 bg-blue-50 text-blue-700';
    case 'published':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    case 'draft':
    default:
      return 'border-slate-200 bg-slate-50 text-slate-700';
  }
}

export function splitStatusTone(status?: string | null): string {
  switch ((status ?? '').toLowerCase()) {
    case 'paid':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'partially_paid':
      return 'border-blue-200 bg-blue-50 text-blue-700';
    case 'disputed':
      return 'border-red-200 bg-red-50 text-red-700';
    case 'waived':
      return 'border-slate-200 bg-slate-100 text-slate-700';
    case 'pending':
    default:
      return 'border-amber-200 bg-amber-50 text-amber-700';
  }
}

export function additionalChargeStatusTone(status?: string | null): string {
  switch ((status ?? '').toLowerCase()) {
    case 'paid':
    case 'accepted':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'partially_accepted':
      return 'border-blue-200 bg-blue-50 text-blue-700';
    case 'disputed':
      return 'border-red-200 bg-red-50 text-red-700';
    case 'waived':
      return 'border-slate-200 bg-slate-100 text-slate-700';
    case 'raised':
    default:
      return 'border-amber-200 bg-amber-50 text-amber-700';
  }
}

export function disputeStatusTone(status?: string | null): string {
  switch ((status ?? '').toLowerCase()) {
    case 'resolved':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'rejected':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    case 'waived':
      return 'border-slate-200 bg-slate-100 text-slate-700';
    case 'open':
    default:
      return 'border-red-200 bg-red-50 text-red-700';
  }
}

export function hasTenantBillingAccess(roles?: string[] | null, isSuperuser?: boolean): boolean {
  if (isSuperuser) {
    return true;
  }

  const normalized = normalizeRoles(roles);
  if (!normalized.length) {
    return true;
  }

  return hasRoleFragment(normalized, ['tenant', 'customer', 'renter']);
}

export function hasBillingManagementAccess(roles?: string[] | null, isSuperuser?: boolean): boolean {
  if (isSuperuser) {
    return true;
  }

  const normalized = normalizeRoles(roles);
  if (!normalized.length) {
    return true;
  }

  return hasRoleFragment(normalized, ['landlord', 'owner', 'admin']);
}
