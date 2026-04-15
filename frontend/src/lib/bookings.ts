import { unwrapApiData } from './properties';
import type {
  AgreementStatus,
  AgreementTemplateSummary,
  BookingEvent,
  BookingListParams,
  BookingListResponse,
  BookingPricing,
  BookingPropertySummary,
  BookingRecord,
  CancellationPolicy,
  RentalAgreement,
  SecurityDeposit,
} from '@/types';

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
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

function toBoolean(value: unknown): boolean | undefined {
  if (typeof value === 'boolean') {
    return value;
  }

  if (typeof value === 'string') {
    if (value === 'true') return true;
    if (value === 'false') return false;
  }

  return undefined;
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

export function buildBookingApiParams(params?: BookingListParams): Record<string, string | number> {
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

export function normalizeBookingPropertySummary(payload: unknown): BookingPropertySummary {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};

  return {
    id: String(record.id ?? record.property_id ?? record.propertyId ?? ''),
    name: String(record.name ?? record.property_name ?? record.propertyName ?? 'Property'),
    location_address: toOptionalString(
      record.location_address ??
        record.locationAddress ??
        (isRecord(record.location) ? record.location.address : undefined)
    ),
  };
}

export function normalizeBookingPricing(payload: unknown): BookingPricing {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};

  return {
    currency: toOptionalString(record.currency) ?? 'NPR',
    base_fee: toNumber(record.base_fee ?? record.baseFee) ?? 0,
    peak_surcharge: toNumber(record.peak_surcharge ?? record.peakSurcharge) ?? 0,
    tax_amount: toNumber(record.tax_amount ?? record.taxAmount) ?? 0,
    total_fee:
      toNumber(record.total_fee ?? record.totalFee ?? record.total_due ?? record.totalDue) ?? 0,
    deposit_amount: toNumber(record.deposit_amount ?? record.depositAmount) ?? 0,
    total_due_now:
      toNumber(
        record.total_due_now ??
          record.totalDueNow ??
          record.total_due ??
          record.totalDue ??
          record.total_fee ??
          record.totalFee
      ) ?? 0,
  };
}

export function normalizeCancellationPolicy(payload: unknown): CancellationPolicy {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};

  return {
    name: toOptionalString(record.name) ?? 'Standard cancellation policy',
    free_cancellation_hours:
      toNumber(record.free_cancellation_hours ?? record.freeCancellationHours) ?? 72,
    partial_refund_hours:
      toNumber(record.partial_refund_hours ?? record.partialRefundHours) ?? 24,
    partial_refund_percent:
      toNumber(record.partial_refund_percent ?? record.partialRefundPercent) ?? 50,
  };
}

export function normalizeSecurityDeposit(payload: unknown): SecurityDeposit {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};

  return {
    id: String(record.id ?? ''),
    booking_id: String(record.booking_id ?? record.bookingId ?? ''),
    amount: toNumber(record.amount) ?? 0,
    status: String(record.status ?? 'held'),
    gateway_ref: toOptionalString(record.gateway_ref ?? record.gatewayRef),
    deduction_total: toNumber(record.deduction_total ?? record.deductionTotal) ?? 0,
    refund_amount: toNumber(record.refund_amount ?? record.refundAmount) ?? 0,
    collected_at: toOptionalString(record.collected_at ?? record.collectedAt),
    settled_at: toOptionalString(record.settled_at ?? record.settledAt),
  };
}

export function normalizeBooking(payload: unknown): BookingRecord {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};
  const propertySource =
    record.property ??
    ({
      id: record.property_id ?? record.propertyId,
      name: record.property_name ?? record.propertyName,
      location_address: record.location_address ?? record.locationAddress,
    } satisfies UnknownRecord);

  const pricingSource = record.pricing ?? record.quote ?? record.pricing_preview ?? {};
  const policySource = record.cancellation_policy ?? record.cancellationPolicy ?? {};
  const agreementSource = isRecord(record.agreement) ? record.agreement : null;
  const agreementStatus =
    toOptionalString(record.agreement_status ?? record.agreementStatus ?? agreementSource?.status) ??
    null;
  const securityDepositSource = record.security_deposit ?? record.securityDeposit;

  return {
    id: String(record.id ?? record.booking_id ?? ''),
    booking_number: String(
      record.booking_number ?? record.bookingNumber ?? `BK-${record.id ?? record.booking_id ?? 'draft'}`
    ),
    status: String(record.status ?? 'pending'),
    property: normalizeBookingPropertySummary(propertySource),
    tenant_user_id: String(record.tenant_user_id ?? record.tenantUserId ?? ''),
    owner_user_id: String(record.owner_user_id ?? record.ownerUserId ?? ''),
    rental_start_at: toOptionalString(record.rental_start_at ?? record.rentalStartAt) ?? '',
    rental_end_at: toOptionalString(record.rental_end_at ?? record.rentalEndAt) ?? '',
    actual_return_at: toOptionalString(record.actual_return_at ?? record.actualReturnAt),
    special_requests:
      toOptionalString(record.special_requests ?? record.specialRequests) ?? '',
    pricing: normalizeBookingPricing(pricingSource),
    security_deposit: securityDepositSource
      ? normalizeSecurityDeposit(securityDepositSource)
      : null,
    cancellation_policy: normalizeCancellationPolicy(policySource),
    decline_reason: toOptionalString(record.decline_reason ?? record.declineReason) ?? '',
    cancellation_reason:
      toOptionalString(record.cancellation_reason ?? record.cancellationReason) ?? '',
    cancelled_at: toOptionalString(record.cancelled_at ?? record.cancelledAt),
    confirmed_at: toOptionalString(record.confirmed_at ?? record.confirmedAt),
    declined_at: toOptionalString(record.declined_at ?? record.declinedAt),
    refund_amount: toNumber(record.refund_amount ?? record.refundAmount) ?? 0,
    agreement_status: agreementStatus,
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? undefined,
    updated_at: toOptionalString(record.updated_at ?? record.updatedAt) ?? undefined,
  };
}

export function normalizeBookingListResponse(payload: unknown): BookingListResponse {
  const data = unwrapApiData(payload);

  if (Array.isArray(data)) {
    return {
      items: data.map(normalizeBooking),
      total: data.length,
      page: 1,
      per_page: data.length || 20,
      has_more: false,
    };
  }

  const record = isRecord(data) ? data : {};
  const root = isRecord(payload) ? payload : {};
  const meta = isRecord(root.meta) ? root.meta : {};
  const items = getArray(record.items ?? record.bookings ?? record.results ?? record.data ?? []).map(
    normalizeBooking
  );
  const total =
    toNumber(record.total ?? record.count ?? meta.total ?? meta.count) ?? items.length;
  const page =
    toNumber(record.page ?? record.current_page ?? record.currentPage ?? meta.page ?? meta.current_page) ??
    1;
  const perPage =
    toNumber(record.per_page ?? record.perPage ?? record.limit ?? meta.per_page ?? meta.perPage) ??
    (items.length || 20);
  const hasMore =
    toBoolean(record.has_more ?? record.hasMore) ?? page * perPage < total;

  return {
    items,
    total,
    page,
    per_page: perPage,
    has_more: hasMore,
  };
}

export function normalizeBookingEvent(payload: unknown): BookingEvent {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};

  return {
    id: String(record.id ?? `${record.booking_id ?? 'booking'}-${record.event_type ?? 'event'}`),
    booking_id: String(record.booking_id ?? record.bookingId ?? ''),
    event_type: String(record.event_type ?? record.eventType ?? 'status.updated'),
    message: String(record.message ?? record.description ?? 'Status updated'),
    actor_user_id: toOptionalString(record.actor_user_id ?? record.actorUserId),
    metadata_json: isRecord(record.metadata_json ?? record.metadataJson)
      ? (record.metadata_json ?? record.metadataJson) as Record<string, unknown>
      : null,
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? undefined,
  };
}

export function normalizeBookingEvents(payload: unknown): BookingEvent[] {
  const data = unwrapApiData(payload);
  const source = Array.isArray(data)
    ? data
    : getArray(
        (isRecord(data) ? data.events ?? data.items ?? data.results : undefined) ?? []
      );

  return source
    .map(normalizeBookingEvent)
    .sort((left, right) => {
      const leftTime = left.created_at ? new Date(left.created_at).getTime() : 0;
      const rightTime = right.created_at ? new Date(right.created_at).getTime() : 0;
      return leftTime - rightTime;
    });
}

export function normalizeAgreementTemplateSummary(payload: unknown): AgreementTemplateSummary {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};

  return {
    id: String(record.id ?? ''),
    property_type_id: String(record.property_type_id ?? record.propertyTypeId ?? ''),
    name: String(record.name ?? 'Default template'),
    version: toNumber(record.version) ?? 1,
  };
}

export function normalizeRentalAgreement(payload: unknown): RentalAgreement {
  const data = unwrapApiData(payload);
  const root = isRecord(data) ? data : {};
  const record = isRecord(root.agreement) ? root.agreement : root;
  const templateSource = record.template ?? record.template_summary ?? {};

  return {
    id: String(record.id ?? ''),
    booking_id: String(record.booking_id ?? record.bookingId ?? root.booking_id ?? root.bookingId ?? ''),
    template: normalizeAgreementTemplateSummary(templateSource),
    status: String(record.status ?? 'draft') as AgreementStatus,
    rendered_content: toOptionalString(record.rendered_content ?? record.renderedContent) ?? '',
    custom_clauses: getArray(record.custom_clauses ?? record.customClauses).map(String),
    rendered_document_url: toOptionalString(
      record.rendered_document_url ?? record.renderedDocumentUrl
    ),
    rendered_document_sha256: toOptionalString(
      record.rendered_document_sha256 ?? record.renderedDocumentSha256
    ),
    esign_request_id: toOptionalString(record.esign_request_id ?? record.esignRequestId),
    signed_document_url: toOptionalString(record.signed_document_url ?? record.signedDocumentUrl),
    signed_document_sha256: toOptionalString(
      record.signed_document_sha256 ?? record.signedDocumentSha256
    ),
    sent_at: toOptionalString(record.sent_at ?? record.sentAt),
    customer_signed_at: toOptionalString(record.customer_signed_at ?? record.customerSignedAt),
    customer_signature_ip: toOptionalString(
      record.customer_signature_ip ?? record.customerSignatureIp
    ),
    owner_signed_at: toOptionalString(record.owner_signed_at ?? record.ownerSignedAt),
    owner_signature_ip: toOptionalString(record.owner_signature_ip ?? record.ownerSignatureIp),
    version: toNumber(record.version) ?? 1,
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? undefined,
  };
}

export function formatBookingStatus(status?: string | null): string {
  return humanize(status ?? 'pending');
}

export function formatAgreementStatus(status?: string | null): string {
  return humanize(status ?? 'draft');
}

export function formatEventType(eventType?: string | null): string {
  return humanize(eventType ?? 'status.updated');
}

export function formatBookingDateTime(value?: string | null): string {
  if (!value) {
    return '—';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('en-NP', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function formatBookingWindow(start?: string | null, end?: string | null): string {
  if (!start && !end) {
    return '—';
  }

  return `${formatBookingDateTime(start)} → ${formatBookingDateTime(end)}`;
}

export function bookingStatusTone(status?: string | null): string {
  switch (status) {
    case 'confirmed':
    case 'active':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'pending_closure':
      return 'border-blue-200 bg-blue-50 text-blue-700';
    case 'declined':
    case 'cancelled':
      return 'border-red-200 bg-red-50 text-red-700';
    case 'closed':
      return 'border-slate-200 bg-slate-50 text-slate-700';
    case 'pending':
    default:
      return 'border-amber-200 bg-amber-50 text-amber-700';
  }
}

export function agreementStatusTone(status?: string | null): string {
  switch (status) {
    case 'signed':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'pending_owner_signature':
      return 'border-blue-200 bg-blue-50 text-blue-700';
    case 'pending_customer_signature':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    case 'amended':
      return 'border-violet-200 bg-violet-50 text-violet-700';
    case 'terminated':
      return 'border-red-200 bg-red-50 text-red-700';
    case 'draft':
    default:
      return 'border-slate-200 bg-slate-50 text-slate-700';
  }
}

export function hasBookingViewAccess(roles?: string[] | null, isSuperuser?: boolean): boolean {
  if (isSuperuser) {
    return true;
  }

  const normalized = normalizeRoles(roles);
  if (!normalized.length) {
    return true;
  }

  return hasRoleFragment(normalized, ['tenant', 'customer', 'renter', 'landlord', 'owner', 'admin']);
}

export function hasBookingManagementAccess(
  roles?: string[] | null,
  isSuperuser?: boolean
): boolean {
  if (isSuperuser) {
    return true;
  }

  const normalized = normalizeRoles(roles);
  if (!normalized.length) {
    return true;
  }

  return hasRoleFragment(normalized, ['landlord', 'owner', 'admin']);
}

export function canCreateBooking(roles?: string[] | null, isSuperuser?: boolean): boolean {
  if (isSuperuser) {
    return true;
  }

  const normalized = normalizeRoles(roles);
  if (!normalized.length) {
    return true;
  }

  return hasRoleFragment(normalized, ['tenant', 'customer', 'renter']);
}
