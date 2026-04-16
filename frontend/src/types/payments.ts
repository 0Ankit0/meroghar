// Finance / Payments and billing module types

export type PaymentProvider = 'khalti' | 'esewa' | 'stripe' | 'paypal';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded' | 'cancelled' | string;

export interface InitiatePaymentRequest {
  provider: PaymentProvider;
  amount: number;
  purchase_order_id: string;
  purchase_order_name: string;
  return_url: string;
  website_url?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
}

export interface InitiatePaymentResponse {
  transaction_id: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  payment_url?: string;
  provider_pidx?: string;
  extra?: Record<string, unknown>;
}

export interface VerifyPaymentRequest {
  provider: PaymentProvider;
  pidx?: string; // Khalti
  oid?: string; // eSewa legacy
  refId?: string; // eSewa legacy
  data?: string; // eSewa v2 base64-encoded callback data
  transaction_id?: string;
}

export interface VerifyPaymentResponse {
  transaction_id: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  amount?: number;
  provider_transaction_id?: string;
  extra?: Record<string, unknown>;
}

export interface PaymentTransaction {
  id: string;
  provider: PaymentProvider;
  status: PaymentStatus;
  amount: number;
  currency: string;
  purchase_order_id: string;
  purchase_order_name: string;
  provider_transaction_id?: string;
  provider_pidx?: string;
  return_url: string;
  website_url: string;
  failure_reason?: string;
  created_at: string;
  updated_at: string;
}

export type InvoiceStatus =
  | 'draft'
  | 'sent'
  | 'partially_paid'
  | 'paid'
  | 'overdue'
  | 'waived'
  | string;

export type InvoiceType = 'rent' | 'additional_charge' | 'utility_bill_share' | string;
export type InvoiceReminderType = 't_minus_7' | 't_minus_3' | 't_minus_1' | 'overdue' | string;
export type InvoiceReminderStatus = 'scheduled' | 'sent' | 'skipped' | string;
export type PaymentReferenceType = 'invoice' | 'security_deposit' | string;

export interface InvoiceLineItem {
  id: string;
  invoice_id: string;
  line_item_type: string;
  description: string;
  amount: number;
  tax_rate: number;
  tax_amount: number;
  metadata_json?: Record<string, unknown> | null;
}

export interface InvoiceReminder {
  id: string;
  invoice_id: string;
  reminder_type: InvoiceReminderType;
  scheduled_for: string;
  sent_at?: string | null;
  status: InvoiceReminderStatus;
  channel_status_json?: Record<string, unknown> | null;
}

export interface InvoicePaymentRecord {
  id: string;
  reference_type: PaymentReferenceType;
  reference_id: string;
  payer_user_id: string;
  payment_method: PaymentProvider | string;
  status: PaymentStatus;
  amount: number;
  currency: string;
  gateway_ref: string;
  gateway_response_json?: Record<string, unknown> | null;
  is_offline: boolean;
  created_at: string;
  confirmed_at?: string | null;
}

export interface InvoiceRecord {
  id: string;
  invoice_number: string;
  booking_id?: string | null;
  tenant_user_id: string;
  owner_user_id: string;
  invoice_type: InvoiceType;
  currency: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  status: InvoiceStatus;
  due_date: string;
  period_start?: string | null;
  period_end?: string | null;
  metadata_json?: Record<string, unknown> | null;
  line_items: InvoiceLineItem[];
  reminders: InvoiceReminder[];
  payments: InvoicePaymentRecord[];
  created_at: string;
  paid_at?: string | null;
}

export interface InvoiceListResponse {
  items: InvoiceRecord[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface InvoiceListParams {
  page?: number;
  per_page?: number;
  status?: InvoiceStatus | 'all' | '';
}

export interface InvoicePaymentPayload {
  provider: PaymentProvider;
  amount?: number | null;
  return_url: string;
  website_url?: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
}

export type AdditionalChargeStatus =
  | 'raised'
  | 'accepted'
  | 'disputed'
  | 'partially_accepted'
  | 'paid'
  | 'waived'
  | string;

export interface AdditionalChargeRecord {
  id: string;
  booking_id: string;
  invoice_id?: string | null;
  charge_type: string;
  description: string;
  amount: number;
  resolved_amount?: number | null;
  evidence_url: string;
  status: AdditionalChargeStatus;
  dispute_reason: string;
  resolution_notes: string;
  created_at: string;
  resolved_at?: string | null;
}

export interface AdditionalChargeCreatePayload {
  charge_type?: string;
  description: string;
  amount: number;
  evidence_url?: string;
}

export interface AdditionalChargeDisputePayload {
  reason: string;
}

export interface AdditionalChargeResolvePayload {
  outcome: AdditionalChargeStatus;
  resolved_amount?: number | null;
  resolution_notes?: string;
}

export interface RentLedgerEntry {
  period_start: string;
  period_end: string;
  amount_due: number;
  invoice_id?: string | null;
  invoice_status?: InvoiceStatus | null;
  due_date?: string | null;
  paid_amount: number;
  outstanding_amount: number;
}

export interface RentLedger {
  booking_id: string;
  currency: string;
  entries: RentLedgerEntry[];
  additional_charges: AdditionalChargeRecord[];
  total_amount: number;
  paid_amount: number;
  outstanding_amount: number;
}

export type UtilityBillType = 'electricity' | 'water' | 'internet' | 'gas' | 'other' | string;
export type UtilityBillStatus = 'draft' | 'published' | 'partially_paid' | 'settled' | string;
export type UtilityBillSplitMethod = 'single' | 'equal' | 'percentage' | 'fixed' | string;
export type UtilityBillSplitStatus = 'pending' | 'partially_paid' | 'paid' | 'disputed' | 'waived' | string;
export type UtilityBillDisputeStatus = 'open' | 'resolved' | 'rejected' | 'waived' | string;

export interface UtilityBillAttachment {
  id: string;
  utility_bill_id: string;
  file_url: string;
  file_type: string;
  checksum: string;
  uploaded_at: string;
}

export interface UtilityBillSplit {
  id: string;
  utility_bill_id: string;
  tenant_user_id: string;
  invoice_id?: string | null;
  split_method: UtilityBillSplitMethod;
  split_percent?: number | null;
  assigned_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  status: UtilityBillSplitStatus;
  due_at?: string | null;
  paid_at?: string | null;
}

export interface UtilityBillDispute {
  id: string;
  utility_bill_split_id: string;
  opened_by_user_id: string;
  status: UtilityBillDisputeStatus;
  reason: string;
  resolution_notes: string;
  opened_at: string;
  resolved_at?: string | null;
}

export interface UtilityBillRecord {
  id: string;
  property_id: string;
  created_by_user_id: string;
  bill_type: UtilityBillType;
  billing_period_label: string;
  period_start: string;
  period_end: string;
  due_date: string;
  total_amount: number;
  owner_subsidy_amount: number;
  payable_amount: number;
  status: UtilityBillStatus;
  notes: string;
  attachments: UtilityBillAttachment[];
  splits: UtilityBillSplit[];
  created_at: string;
  published_at?: string | null;
}

export interface UtilityBillListResponse {
  items: UtilityBillRecord[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface UtilityBillShareRecord {
  split: UtilityBillSplit;
  bill: UtilityBillRecord;
  disputes: UtilityBillDispute[];
}

export interface UtilityBillShareListResponse {
  items: UtilityBillShareRecord[];
  total: number;
}

export interface UtilityBillCreatePayload {
  bill_type: UtilityBillType;
  billing_period_label: string;
  period_start: string;
  period_end: string;
  due_date: string;
  total_amount: number;
  owner_subsidy_amount?: number;
  notes?: string;
}

export interface UtilityBillAttachmentUploadPayload {
  file: File;
}

export interface UtilityBillSplitInput {
  tenant_user_id: string;
  split_method: UtilityBillSplitMethod;
  split_percent?: number | null;
  assigned_amount?: number | null;
}

export interface UtilityBillSplitConfigurePayload {
  default_method?: UtilityBillSplitMethod | null;
  splits: UtilityBillSplitInput[];
}

export interface UtilityBillDisputePayload {
  reason: string;
}

export interface UtilityBillDisputeResolvePayload {
  outcome: UtilityBillDisputeStatus;
  resolution_notes?: string;
}

export interface UtilityBillHistoryEntry {
  event_type: string;
  message: string;
  occurred_at: string;
  metadata_json?: Record<string, unknown> | null;
}

export interface UtilityBillHistory {
  bill_id: string;
  entries: UtilityBillHistoryEntry[];
}
