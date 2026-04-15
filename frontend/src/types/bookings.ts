export type BookingStatus =
  | 'pending'
  | 'confirmed'
  | 'declined'
  | 'cancelled'
  | 'active'
  | 'pending_closure'
  | 'closed'
  | string;

export type SecurityDepositStatus =
  | 'held'
  | 'fully_refunded'
  | 'partially_refunded'
  | 'fully_deducted'
  | 'disputed'
  | string;

export type AgreementStatus =
  | 'draft'
  | 'pending_customer_signature'
  | 'pending_owner_signature'
  | 'signed'
  | 'amended'
  | 'terminated'
  | string;

export interface BookingPropertySummary {
  id: string;
  name: string;
  location_address?: string | null;
}

export interface BookingPricing {
  currency: string;
  base_fee: number;
  peak_surcharge: number;
  tax_amount: number;
  total_fee: number;
  deposit_amount: number;
  total_due_now: number;
}

export interface CancellationPolicy {
  name: string;
  free_cancellation_hours: number;
  partial_refund_hours: number;
  partial_refund_percent: number;
}

export interface SecurityDeposit {
  id: string;
  booking_id: string;
  amount: number;
  status: SecurityDepositStatus;
  gateway_ref?: string | null;
  deduction_total: number;
  refund_amount: number;
  collected_at?: string | null;
  settled_at?: string | null;
}

export interface BookingRecord {
  id: string;
  booking_number: string;
  status: BookingStatus;
  property: BookingPropertySummary;
  tenant_user_id: string;
  owner_user_id: string;
  rental_start_at: string;
  rental_end_at: string;
  actual_return_at?: string | null;
  special_requests: string;
  pricing: BookingPricing;
  security_deposit?: SecurityDeposit | null;
  cancellation_policy: CancellationPolicy;
  decline_reason: string;
  cancellation_reason: string;
  cancelled_at?: string | null;
  confirmed_at?: string | null;
  declined_at?: string | null;
  refund_amount: number;
  agreement_status?: AgreementStatus | null;
  created_at?: string;
  updated_at?: string;
}

export interface BookingListResponse {
  items: BookingRecord[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface BookingEvent {
  id: string;
  booking_id: string;
  event_type: string;
  message: string;
  actor_user_id?: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at?: string;
}

export interface BookingListParams {
  page?: number;
  per_page?: number;
  status?: BookingStatus | 'all' | '';
}

export interface CreateBookingPayload {
  property_id: string;
  rental_start_at: string;
  rental_end_at: string;
  special_requests?: string;
  payment_method_id: string;
  quoted_total_fee?: number | null;
  quoted_deposit_amount?: number | null;
  quoted_currency?: string | null;
}

export interface UpdateBookingPayload {
  rental_start_at?: string;
  rental_end_at?: string;
  special_requests?: string;
  quoted_total_fee?: number | null;
  quoted_deposit_amount?: number | null;
  quoted_currency?: string | null;
}

export interface BookingDeclinePayload {
  reason: string;
}

export interface BookingCancelPayload {
  reason: string;
}

export interface BookingReturnPayload {
  actual_return_at?: string | null;
  notes?: string;
}

export interface AgreementTemplateSummary {
  id: string;
  property_type_id: string;
  name: string;
  version: number;
}

export interface RentalAgreement {
  id: string;
  booking_id: string;
  template: AgreementTemplateSummary;
  status: AgreementStatus;
  rendered_content: string;
  custom_clauses: string[];
  rendered_document_url?: string | null;
  rendered_document_sha256?: string | null;
  esign_request_id?: string | null;
  signed_document_url?: string | null;
  signed_document_sha256?: string | null;
  sent_at?: string | null;
  customer_signed_at?: string | null;
  customer_signature_ip?: string | null;
  owner_signed_at?: string | null;
  owner_signature_ip?: string | null;
  version: number;
  created_at?: string;
}

export interface AgreementGeneratePayload {
  template_id?: string | null;
  custom_clauses?: string[];
}
