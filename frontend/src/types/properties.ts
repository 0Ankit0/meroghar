export type PropertyStatus =
  | 'draft'
  | 'published'
  | 'unpublished'
  | 'archived'
  | 'available'
  | 'maintenance'
  | string;

export type PricingRateType = 'hourly' | 'daily' | 'weekly' | 'monthly' | string;
export type AvailabilityBlockType = 'booking' | 'maintenance' | 'manual' | string;
export type CategoryAttributeType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'integer'
  | 'boolean'
  | 'select'
  | 'multiselect'
  | 'date'
  | 'datetime'
  | string;

export interface CategoryAttributeOption {
  label: string;
  value: string;
}

export interface PropertyCategoryAttribute {
  id: string;
  category_id: string;
  name: string;
  slug: string;
  attribute_type: CategoryAttributeType;
  is_required: boolean;
  is_filterable: boolean;
  options_json?: Array<string | CategoryAttributeOption> | Record<string, unknown> | null;
  display_order?: number;
}

export interface PropertyCategory {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  icon_url?: string | null;
  parent_category_id?: string | null;
  is_active?: boolean;
  display_order?: number;
}

export interface PropertyCategoryDetail extends PropertyCategory {
  attributes: PropertyCategoryAttribute[];
}

export interface PropertyPhoto {
  id: string;
  property_id?: string;
  url: string;
  thumbnail_url?: string | null;
  position?: number;
  is_cover?: boolean;
  caption?: string | null;
}

export interface PropertyAttributeValue {
  id?: string;
  property_id?: string;
  attribute_id: string;
  attribute_name?: string;
  attribute_slug?: string;
  value: string | number | boolean | string[] | null;
}

export interface PricingQuote {
  base_fee: number;
  rate_type?: PricingRateType | null;
  rate_units?: number | null;
  peak_surcharge?: number | null;
  discount_amount?: number | null;
  tax_amount?: number | null;
  deposit_amount?: number | null;
  total_due: number;
  currency: string;
}

export interface PropertySummary {
  id: string;
  owner_user_id?: string;
  category_id?: string;
  category?: PropertyCategory | null;
  name: string;
  description?: string | null;
  status?: PropertyStatus;
  is_published?: boolean;
  location_address?: string | null;
  location_lat?: number | null;
  location_lng?: number | null;
  deposit_amount?: number | null;
  min_rental_duration_hours?: number | null;
  max_rental_duration_days?: number | null;
  booking_lead_time_hours?: number | null;
  instant_booking_enabled?: boolean;
  average_rating?: number | null;
  review_count?: number | null;
  photos?: PropertyPhoto[];
  attributes?: PropertyAttributeValue[];
  pricing_preview?: PricingQuote | null;
  created_at?: string;
  updated_at?: string;
}

export interface AvailabilityBlock {
  id: string;
  property_id?: string;
  block_type: AvailabilityBlockType;
  start_at: string;
  end_at: string;
  reason?: string | null;
  booking_id?: string | null;
  maintenance_request_id?: string | null;
}

export interface PropertyDetail extends PropertySummary {
  availability_blocks?: AvailabilityBlock[];
}

export interface PropertySearchParams {
  category?: string;
  start?: string;
  end?: string;
  location?: string;
  radius_km?: number;
  min_price?: number;
  max_price?: number;
  page?: number;
  per_page?: number;
}

export interface PropertyListResponse {
  items: PropertySummary[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface PropertyAvailabilityResponse {
  property_id: string;
  range_start?: string;
  range_end?: string;
  is_available?: boolean;
  next_available_start?: string | null;
  blocks: AvailabilityBlock[];
}

export interface PropertyPriceQuoteParams {
  start: string;
  end: string;
}

export interface PricingRule {
  id: string;
  property_id?: string;
  rate_type: PricingRateType;
  rate_amount: number;
  currency: string;
  is_peak_rate: boolean;
  peak_start_date?: string | null;
  peak_end_date?: string | null;
  peak_days_of_week?: string[];
  discount_percentage?: number | null;
  min_units_for_discount?: number | null;
  created_at?: string;
}

export interface PricingRuleInput {
  rate_type: PricingRateType;
  rate_amount: number;
  currency: string;
  is_peak_rate: boolean;
  peak_start_date?: string | null;
  peak_end_date?: string | null;
  peak_days_of_week_json?: number[];
  discount_percentage?: number | null;
  min_units_for_discount?: number | null;
}

export interface AvailabilityBlockInput {
  id?: string;
  block_type: AvailabilityBlockType;
  start_at: string;
  end_at: string;
  reason?: string | null;
}

export interface PropertyAttributeValueInput {
  attribute_id: string;
  value: string | number | boolean | string[] | null;
}

export interface PropertyMutationPayload {
  category_id: string;
  name: string;
  description: string;
  location_address: string;
  location_lat?: number | null;
  location_lng?: number | null;
  deposit_amount: number;
  min_rental_duration_hours: number;
  max_rental_duration_days: number;
  booking_lead_time_hours: number;
  instant_booking_enabled: boolean;
  attribute_values?: PropertyAttributeValueInput[];
  availability_blocks?: AvailabilityBlockInput[];
}

export interface PropertyPhotoUploadPayload {
  file: File;
  caption?: string;
  is_cover?: boolean;
  position?: number;
}
