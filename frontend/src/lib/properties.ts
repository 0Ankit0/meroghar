import type {
  AvailabilityBlock,
  CategoryAttributeOption,
  PricingQuote,
  PricingRule,
  PropertyAttributeValue,
  PropertyAvailabilityResponse,
  PropertyCategory,
  PropertyCategoryAttribute,
  PropertyCategoryDetail,
  PropertyDetail,
  PropertyListResponse,
  PropertyPhoto,
  PropertySearchParams,
  PropertySummary,
} from '@/types';

type UnknownRecord = Record<string, unknown>;

interface ApiEnvelope<T> {
  success?: boolean;
  data?: T;
  meta?: UnknownRecord;
}

const DAY_OF_WEEK_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;

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
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function unwrapApiData<T>(payload: T | ApiEnvelope<T>): T {
  if (isApiEnvelope<T>(payload)) {
    return payload.data as T;
  }

  return payload as T;
}

export function normalizeCategoryAttributeOptions(options: unknown): CategoryAttributeOption[] {
  if (Array.isArray(options)) {
    return options
      .map((option) => {
        if (typeof option === 'string') {
          return { label: humanize(option), value: option };
        }

        if (isRecord(option)) {
          const value = toOptionalString(option.value ?? option.id ?? option.label);
          const label = toOptionalString(option.label ?? option.name ?? option.value ?? option.id);
          if (value && label) {
            return { label, value };
          }
        }

        return null;
      })
      .filter((option): option is CategoryAttributeOption => Boolean(option));
  }

  if (isRecord(options)) {
    return Object.entries(options).map(([value, label]) => ({
      value,
      label: typeof label === 'string' ? label : humanize(value),
    }));
  }

  return [];
}

export function normalizePropertyCategoryAttribute(payload: unknown): PropertyCategoryAttribute {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? record.attribute_id ?? record.slug ?? ''),
    category_id: String(record.category_id ?? record.property_type_id ?? record.categoryId ?? ''),
    name: String(record.name ?? record.label ?? record.slug ?? 'Attribute'),
    slug: String(record.slug ?? record.name ?? record.id ?? 'attribute').toLowerCase().replace(/\s+/g, '-'),
    attribute_type: String(record.attribute_type ?? record.attributeType ?? record.type ?? 'text'),
    is_required: Boolean(record.is_required ?? record.isRequired),
    is_filterable: Boolean(record.is_filterable ?? record.isFilterable),
    options_json: (record.options_json ?? record.options ?? null) as PropertyCategoryAttribute['options_json'],
    display_order: toNumber(record.display_order ?? record.displayOrder) ?? undefined,
  };
}

export function normalizePropertyCategory(payload: unknown): PropertyCategory {
  const record = isRecord(payload) ? payload : {};

  return {
    id: String(record.id ?? record.category_id ?? record.slug ?? ''),
    name: String(record.name ?? record.title ?? record.slug ?? 'Category'),
    slug: String(record.slug ?? record.name ?? record.id ?? 'category').toLowerCase().replace(/\s+/g, '-'),
    description: toOptionalString(record.description),
    icon_url: toOptionalString(record.icon_url ?? record.iconUrl),
    parent_category_id: toOptionalString(record.parent_category_id ?? record.parentCategoryId),
    is_active: toBoolean(record.is_active ?? record.isActive),
    display_order: toNumber(record.display_order ?? record.displayOrder) ?? undefined,
  };
}

export function normalizePropertyCategoryDetail(payload: unknown): PropertyCategoryDetail {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};
  const category = normalizePropertyCategory(record);
  const attributes = getArray(
    record.attributes ?? record.property_type_features ?? record.features ?? []
  ).map(normalizePropertyCategoryAttribute);

  return {
    ...category,
    attributes,
  };
}

export function normalizePropertyCategories(payload: unknown): PropertyCategory[] {
  const data = unwrapApiData(payload);

  if (Array.isArray(data)) {
    return data.map(normalizePropertyCategory);
  }

  const record = isRecord(data) ? data : {};
  const items = getArray(record.items ?? record.results ?? record.categories ?? record.data ?? []);
  return items.map(normalizePropertyCategory);
}

export function normalizePropertyPhoto(payload: unknown): PropertyPhoto {
  const record = isRecord(payload) ? payload : {};
  const url = toOptionalString(record.url ?? record.image_url ?? record.imageUrl) ?? '';

  return {
    id: String(record.id ?? url ?? `photo-${Math.random().toString(36).slice(2)}`),
    property_id: toOptionalString(record.property_id ?? record.propertyId) ?? undefined,
    url,
    thumbnail_url: toOptionalString(record.thumbnail_url ?? record.thumbnailUrl),
    position: toNumber(record.position) ?? undefined,
    is_cover: toBoolean(record.is_cover ?? record.isCover),
    caption: toOptionalString(record.caption),
  };
}

export function normalizePropertyAttributeValue(payload: unknown): PropertyAttributeValue {
  const record = isRecord(payload) ? payload : {};
  const rawValue = record.value ?? record.attribute_value ?? null;

  return {
    id: toOptionalString(record.id) ?? undefined,
    property_id: toOptionalString(record.property_id ?? record.propertyId) ?? undefined,
    attribute_id: String(record.attribute_id ?? record.attributeId ?? record.id ?? ''),
    attribute_name: toOptionalString(
      record.attribute_name ?? record.name ?? (isRecord(record.attribute) ? record.attribute.name : undefined)
    ) ?? undefined,
    attribute_slug: toOptionalString(
      record.attribute_slug ?? record.slug ?? (isRecord(record.attribute) ? record.attribute.slug : undefined)
    ) ?? undefined,
    value: Array.isArray(rawValue)
      ? rawValue.map(String)
      : typeof rawValue === 'string' || typeof rawValue === 'number' || typeof rawValue === 'boolean'
        ? rawValue
        : rawValue === null || rawValue === undefined
          ? null
          : JSON.stringify(rawValue),
  };
}

export function normalizePropertyPriceQuote(
  payload: unknown,
  options: { preferDueNow?: boolean } = {}
): PricingQuote {
  const data = unwrapApiData(payload);
  const record = isRecord(data) ? data : {};
  const totalDue = options.preferDueNow
    ? toNumber(
        record.total_due_now ??
          record.totalDueNow ??
          record.total_due ??
          record.totalDue ??
          record.total_fee ??
          record.totalFee
      )
    : toNumber(
        record.total_due ??
          record.totalDue ??
          record.total_fee ??
          record.totalFee ??
          record.total_due_now ??
          record.totalDueNow
      );

  return {
    base_fee: toNumber(record.base_fee ?? record.baseFee) ?? 0,
    rate_type: toOptionalString(record.rate_type ?? record.rateType),
    rate_units: toNumber(record.rate_units ?? record.rateUnits),
    peak_surcharge: toNumber(record.peak_surcharge ?? record.peakSurcharge),
    discount_amount: toNumber(record.discount_amount ?? record.discountAmount),
    tax_amount: toNumber(record.tax_amount ?? record.taxAmount),
    deposit_amount: toNumber(record.deposit_amount ?? record.depositAmount),
    total_due: totalDue ?? 0,
    currency: toOptionalString(record.currency) ?? 'NPR',
  };
}

export function normalizePricingRule(payload: unknown): PricingRule {
  const record = isRecord(payload) ? payload : {};
  const peakDays = getArray(
    record.peak_days_of_week_json ?? record.peak_days_of_week ?? record.peakDaysOfWeek
  )
    .map((value) => {
      const dayNumber = toNumber(value);
      if (dayNumber !== null && dayNumber >= 0 && dayNumber < DAY_OF_WEEK_LABELS.length) {
        return DAY_OF_WEEK_LABELS[dayNumber];
      }

      return toOptionalString(value);
    })
    .filter((value): value is string => Boolean(value));

  return {
    id: String(record.id ?? record.rule_id ?? ''),
    property_id: toOptionalString(record.property_id ?? record.propertyId) ?? undefined,
    rate_type: String(record.rate_type ?? record.rateType ?? 'monthly'),
    rate_amount: toNumber(record.rate_amount ?? record.rateAmount) ?? 0,
    currency: toOptionalString(record.currency) ?? 'NPR',
    is_peak_rate: Boolean(record.is_peak_rate ?? record.isPeakRate),
    peak_start_date: toOptionalString(record.peak_start_date ?? record.peakStartDate),
    peak_end_date: toOptionalString(record.peak_end_date ?? record.peakEndDate),
    peak_days_of_week: peakDays,
    discount_percentage: toNumber(record.discount_percentage ?? record.discountPercentage),
    min_units_for_discount: toNumber(record.min_units_for_discount ?? record.minUnitsForDiscount),
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? undefined,
  };
}

export function normalizePropertyPricingRules(payload: unknown): PricingRule[] {
  const data = unwrapApiData(payload);

  if (Array.isArray(data)) {
    return data.map(normalizePricingRule);
  }

  const record = isRecord(data) ? data : {};
  const items = getArray(record.items ?? record.results ?? record.rules ?? record.pricing_rules ?? []);
  return items.map(normalizePricingRule);
}

export function normalizeAvailabilityBlock(payload: unknown): AvailabilityBlock {
  const record = isRecord(payload) ? payload : {};
  const startAt = toOptionalString(record.start_at ?? record.startAt) ?? '';
  const endAt = toOptionalString(record.end_at ?? record.endAt) ?? '';

  return {
    id: String(record.id ?? `${startAt}-${endAt}`),
    property_id: toOptionalString(record.property_id ?? record.propertyId) ?? undefined,
    block_type: String(record.block_type ?? record.type ?? 'manual'),
    start_at: startAt,
    end_at: endAt,
    reason: toOptionalString(record.reason),
    booking_id: toOptionalString(record.booking_id ?? record.bookingId),
    maintenance_request_id: toOptionalString(
      record.maintenance_request_id ?? record.maintenanceRequestId
    ),
  };
}

export function normalizePropertyAvailabilityResponse(
  payload: unknown,
  propertyId?: string
): PropertyAvailabilityResponse {
  const data = unwrapApiData(payload);

  if (Array.isArray(data)) {
    return {
      property_id: propertyId ?? '',
      blocks: data.map(normalizeAvailabilityBlock),
    };
  }

  const record = isRecord(data) ? data : {};
  const blocks = getArray(
    record.blocks ?? record.items ?? record.availability_blocks ?? record.conflicts ?? []
  ).map(normalizeAvailabilityBlock);

  return {
    property_id: String(record.property_id ?? record.propertyId ?? propertyId ?? ''),
    range_start: toOptionalString(record.range_start ?? record.start ?? record.start_at) ?? undefined,
    range_end: toOptionalString(record.range_end ?? record.end ?? record.end_at) ?? undefined,
    is_available: toBoolean(record.is_available ?? record.available),
    next_available_start: toOptionalString(
      record.next_available_start ?? record.nextAvailableStart
    ),
    blocks,
  };
}

export function normalizeProperty(payload: unknown): PropertyDetail {
  const record = isRecord(payload) ? payload : {};
  const categorySource =
    record.category ??
    record.property_type ??
    record.propertyType ??
    (record.property_type_name || record.property_type_slug || record.property_type_id
      ? {
          id: record.property_type_id,
          name: record.property_type_name ?? 'Property',
          slug: record.property_type_slug ?? record.property_type_name ?? 'property',
        }
      : null);
  const rawPhotos = getArray(record.photos ?? record.property_photos ?? record.images);
  const photosSource =
    rawPhotos.length > 0
      ? rawPhotos
      : toOptionalString(record.cover_photo_url ?? record.coverPhotoUrl)
        ? [
            {
              id: `${record.id ?? record.property_id ?? 'property'}-cover`,
              url: toOptionalString(record.cover_photo_url ?? record.coverPhotoUrl),
              thumbnail_url: toOptionalString(record.cover_photo_url ?? record.coverPhotoUrl),
              is_cover: true,
              position: 0,
            },
          ]
        : [];
  const attributesSource = getArray(
    record.attributes ?? record.attribute_values ?? record.feature_values ?? record.property_feature_values
  );
  const availabilitySource = getArray(record.availability_blocks ?? record.blocks ?? record.conflicts);
  const pricingSource = record.pricing_preview ?? record.price_preview ?? record.pricing ?? record.quote;
  const isPublished =
    toBoolean(record.is_published ?? record.isPublished) ??
    (record.property_type_name !== undefined || record.property_type_slug !== undefined ? true : undefined);

  return {
    id: String(record.id ?? record.property_id ?? ''),
    owner_user_id: toOptionalString(record.owner_user_id ?? record.ownerUserId) ?? undefined,
    category_id:
      toOptionalString(record.category_id ?? record.property_type_id ?? record.categoryId) ??
      (categorySource ? normalizePropertyCategory(categorySource).id : undefined),
    category: categorySource ? normalizePropertyCategory(categorySource) : null,
    name: String(record.name ?? record.title ?? 'Untitled property'),
    description: toOptionalString(record.description),
    status:
      toOptionalString(record.status) ??
      (isPublished ? 'published' : 'draft'),
    is_published: isPublished,
    location_address: toOptionalString(
      record.location_address ?? record.locationAddress ?? (isRecord(record.location) ? record.location.address : undefined)
    ),
    location_lat: toNumber(
      record.location_lat ?? record.locationLat ?? (isRecord(record.location) ? record.location.lat ?? record.location.latitude : undefined)
    ),
    location_lng: toNumber(
      record.location_lng ?? record.locationLng ?? (isRecord(record.location) ? record.location.lng ?? record.location.longitude : undefined)
    ),
    deposit_amount: toNumber(record.deposit_amount ?? record.depositAmount),
    min_rental_duration_hours: toNumber(
      record.min_rental_duration_hours ?? record.minRentalDurationHours
    ),
    max_rental_duration_days: toNumber(
      record.max_rental_duration_days ?? record.maxRentalDurationDays
    ),
    booking_lead_time_hours: toNumber(
      record.booking_lead_time_hours ?? record.bookingLeadTimeHours
    ),
    instant_booking_enabled: toBoolean(
      record.instant_booking_enabled ?? record.instantBookingEnabled
    ),
    average_rating: toNumber(record.average_rating ?? record.averageRating),
    review_count: toNumber(record.review_count ?? record.reviewCount),
    photos: photosSource.map(normalizePropertyPhoto),
    attributes: attributesSource.map(normalizePropertyAttributeValue),
    pricing_preview: pricingSource
      ? normalizePropertyPriceQuote(pricingSource)
      : toNumber(record.starting_price) !== null
        ? normalizePropertyPriceQuote({
            total_fee: record.starting_price,
            currency: record.currency,
            deposit_amount: record.deposit_amount,
          })
        : null,
    availability_blocks: availabilitySource.map(normalizeAvailabilityBlock),
    created_at: toOptionalString(record.created_at ?? record.createdAt) ?? undefined,
    updated_at: toOptionalString(record.updated_at ?? record.updatedAt) ?? undefined,
  };
}

export function normalizePropertyListResponse(payload: unknown): PropertyListResponse {
  const envelopeMeta = isApiEnvelope(payload) ? payload.meta : undefined;
  const data = unwrapApiData(payload);

  if (Array.isArray(data)) {
    const items = data.map(normalizeProperty);
    const total = toNumber(envelopeMeta?.total) ?? items.length;
    const page = toNumber(envelopeMeta?.page) ?? 1;
    const perPage = toNumber(envelopeMeta?.per_page ?? envelopeMeta?.perPage) ?? Math.max(items.length, 1);
    return {
      items,
      total,
      page,
      per_page: perPage,
      total_pages: Math.max(1, Math.ceil(total / Math.max(perPage, 1))),
    };
  }

  const record = isRecord(data) ? data : {};
  const dataMeta = isRecord(record.meta) ? record.meta : undefined;
  const items = getArray(record.items ?? record.results ?? record.assets ?? record.properties).map(
    normalizeProperty
  );
  const total =
    toNumber(record.total ?? record.count ?? dataMeta?.total ?? envelopeMeta?.total) ?? items.length;
  const page = toNumber(record.page ?? dataMeta?.page ?? envelopeMeta?.page) ?? 1;
  const perPage =
    toNumber(
      record.per_page ??
        record.perPage ??
        dataMeta?.per_page ??
        dataMeta?.perPage ??
        envelopeMeta?.per_page ??
        envelopeMeta?.perPage
    ) ?? Math.max(items.length, 1);
  const totalPages =
    toNumber(
      record.total_pages ??
        record.totalPages ??
        dataMeta?.total_pages ??
        dataMeta?.totalPages
    ) ?? Math.max(1, Math.ceil(total / Math.max(perPage, 1)));

  return {
    items,
    total,
    page,
    per_page: perPage,
    total_pages: totalPages,
  };
}

export function buildPropertyApiParams(params?: PropertySearchParams): Record<string, string | number> {
  const query: Record<string, string | number> = {};

  if (!params) {
    return query;
  }

  const assign = (key: string, value: unknown) => {
    if (value !== undefined && value !== null && value !== '') {
      query[key] = value as string | number;
    }
  };

  assign('category', params.category);
  assign('location', params.location);
  assign('radius_km', params.radius_km);
  assign('min_price', params.min_price);
  assign('max_price', params.max_price);
  assign('page', params.page);
  assign('per_page', params.per_page);

  const start = toIsoDateTime(params.start);
  const end = toIsoDateTime(params.end);

  assign('start', start ?? params.start);
  assign('end', end ?? params.end);

  return query;
}

export function toIsoDateTime(value?: string | null): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed.toISOString();
}

export function toDateTimeLocalValue(value?: string | null): string {
  if (!value) {
    return '';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return '';
  }

  const pad = (input: number) => input.toString().padStart(2, '0');

  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}T${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`;
}

export function formatMoney(amount?: number | null, currency = 'NPR'): string {
  if (amount === null || amount === undefined || Number.isNaN(amount)) {
    return '—';
  }

  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
}

export function formatDateRange(start?: string | null, end?: string | null): string {
  if (!start && !end) {
    return 'Flexible dates';
  }

  const format = (value?: string | null) => {
    if (!value) {
      return 'Unknown';
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
      return value;
    }

    return parsed.toLocaleString();
  };

  return `${format(start)} → ${format(end)}`;
}

export function formatPropertyStatus(status?: string | null, isPublished?: boolean): string {
  if (!status) {
    return isPublished ? 'Published' : 'Draft';
  }

  return humanize(status);
}

export function propertyStatusTone(status?: string | null, isPublished?: boolean): string {
  const normalized = (status ?? (isPublished ? 'published' : 'draft')).toLowerCase();

  if (['published', 'available', 'active'].includes(normalized)) {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  }

  if (['draft', 'unpublished', 'pending'].includes(normalized)) {
    return 'bg-amber-50 text-amber-700 border-amber-200';
  }

  if (['archived', 'inactive'].includes(normalized)) {
    return 'bg-gray-100 text-gray-700 border-gray-200';
  }

  return 'bg-blue-50 text-blue-700 border-blue-200';
}

export function formatRateType(rateType?: string | null): string {
  if (!rateType) {
    return 'Flexible rate';
  }

  return humanize(rateType);
}

export function formatAvailabilityBlockType(type?: string | null): string {
  if (!type) {
    return 'Block';
  }

  return humanize(type);
}

export function getPropertyCoverPhoto(property: Pick<PropertySummary, 'photos'>): PropertyPhoto | null {
  const photos = property.photos ?? [];
  return photos.find((photo) => photo.is_cover) ?? photos[0] ?? null;
}
