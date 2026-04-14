'use client';

import { useEffect, useMemo, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { AlertCircle, CalendarMinus, Home, Plus, Trash2 } from 'lucide-react';
import { Button, Input, Skeleton } from '@/components/ui';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useCreateListing, usePropertyCategories, usePropertyCategory, useUpdateListing } from '@/hooks/use-properties';
import { normalizeCategoryAttributeOptions, toDateTimeLocalValue, toIsoDateTime } from '@/lib/properties';
import type {
  AvailabilityBlockInput,
  PropertyCategoryAttribute,
  PropertyDetail,
  PropertyMutationPayload,
} from '@/types';

const optionalNumberField = z.preprocess(
  (value) => (value === '' || value === null || value === undefined ? undefined : Number(value)),
  z.number().finite().optional()
);

const listingSchema = z.object({
  category_id: z.string().min(1, 'Property type is required'),
  name: z.string().min(2, 'Listing name is required').max(120),
  description: z
    .string()
    .min(20, 'Provide a short but useful description for renters')
    .max(4000),
  location_address: z.string().min(5, 'Property address is required').max(300),
  location_lat: optionalNumberField,
  location_lng: optionalNumberField,
  deposit_amount: z.coerce.number().min(0, 'Deposit cannot be negative'),
  min_rental_duration_hours: z.coerce.number().int().min(1),
  max_rental_duration_days: z.coerce.number().int().min(1),
  booking_lead_time_hours: z.coerce.number().int().min(0),
  instant_booking_enabled: z.boolean().default(false),
});

type ListingFormValues = z.infer<typeof listingSchema>;
type ListingFormInput = z.input<typeof listingSchema>;
type AttributeFormValue = string | string[] | boolean | undefined;

const MANUAL_BLOCK_OPTIONS = [
  { value: 'manual', label: 'Manual blackout' },
  { value: 'maintenance', label: 'Maintenance hold' },
];

function resolveCategoryId(property?: PropertyDetail) {
  return property?.category_id ?? property?.category?.id ?? '';
}

function buildAttributeState(property?: PropertyDetail) {
  return Object.fromEntries(
    (property?.attributes ?? []).map((attribute) => [
      attribute.attribute_id,
      Array.isArray(attribute.value)
        ? attribute.value
        : typeof attribute.value === 'boolean'
          ? attribute.value
          : attribute.value === null || attribute.value === undefined
            ? undefined
            : String(attribute.value),
    ])
  ) as Record<string, AttributeFormValue>;
}

function buildAvailabilityBlocks(property?: PropertyDetail): AvailabilityBlockInput[] {
  return (property?.availability_blocks ?? [])
    .filter((block) => block.block_type === 'manual' || block.block_type === 'maintenance')
    .map((block) => ({
      id: block.id,
      block_type: block.block_type,
      start_at: toDateTimeLocalValue(block.start_at),
      end_at: toDateTimeLocalValue(block.end_at),
      reason: block.reason ?? '',
    }));
}

function emptyAvailabilityBlock(): AvailabilityBlockInput {
  return {
    block_type: 'manual',
    start_at: '',
    end_at: '',
    reason: '',
  };
}

function normalizeBooleanValue(value: AttributeFormValue) {
  return typeof value === 'boolean' ? value : false;
}

function isAttributeEmpty(value: AttributeFormValue) {
  if (Array.isArray(value)) {
    return value.length === 0;
  }

  if (typeof value === 'boolean') {
    return false;
  }

  return value === undefined || value === '';
}

function serializeAttributeValue(attribute: PropertyCategoryAttribute, value: AttributeFormValue) {
  if (isAttributeEmpty(value)) {
    return null;
  }

  if (attribute.attribute_type === 'boolean') {
    return normalizeBooleanValue(value);
  }

  if (attribute.attribute_type === 'number' || attribute.attribute_type === 'integer') {
    return typeof value === 'string' ? Number(value) : value ?? null;
  }

  if (attribute.attribute_type === 'multiselect') {
    return Array.isArray(value) ? value : [];
  }

  return Array.isArray(value) ? value.join(', ') : String(value);
}

function AttributeField({
  attribute,
  value,
  onChange,
}: {
  attribute: PropertyCategoryAttribute;
  value: AttributeFormValue;
  onChange: (value: AttributeFormValue) => void;
}) {
  const options = normalizeCategoryAttributeOptions(attribute.options_json);
  const commonLabel = (
    <div className="mb-1 flex items-center gap-2">
      <label className="text-sm font-medium text-gray-700">{attribute.name}</label>
      {attribute.is_required ? (
        <span className="rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-600">
          Required
        </span>
      ) : null}
    </div>
  );

  if (attribute.attribute_type === 'boolean') {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        {commonLabel}
        <label className="flex items-center gap-3 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={normalizeBooleanValue(value)}
            onChange={(event) => onChange(event.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Yes
        </label>
      </div>
    );
  }

  if (attribute.attribute_type === 'select' && options.length > 0) {
    return (
      <div>
        {commonLabel}
        <select
          value={typeof value === 'string' ? value : ''}
          onChange={(event) => onChange(event.target.value)}
          className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select an option</option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (attribute.attribute_type === 'multiselect' && options.length > 0) {
    const currentValues = Array.isArray(value) ? value : [];
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-4">
        {commonLabel}
        <div className="flex flex-wrap gap-2">
          {options.map((option) => {
            const selected = currentValues.includes(option.value);
            return (
              <button
                key={option.value}
                type="button"
                onClick={() =>
                  onChange(
                    selected
                      ? currentValues.filter((current) => current !== option.value)
                      : [...currentValues, option.value]
                  )
                }
                className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                  selected
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  if (attribute.attribute_type === 'textarea') {
    return (
      <div className="md:col-span-2">
        {commonLabel}
        <textarea
          rows={4}
          value={typeof value === 'string' ? value : ''}
          onChange={(event) => onChange(event.target.value)}
          placeholder={`Add ${attribute.name.toLowerCase()}`}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    );
  }

  return (
    <Input
      label={attribute.name}
      type={
        attribute.attribute_type === 'number' || attribute.attribute_type === 'integer'
          ? 'number'
          : attribute.attribute_type === 'date'
            ? 'date'
            : attribute.attribute_type === 'datetime'
              ? 'datetime-local'
              : 'text'
      }
      value={typeof value === 'string' ? value : ''}
      onChange={(event) => onChange(event.target.value)}
      placeholder={`Enter ${attribute.name.toLowerCase()}`}
    />
  );
}

export function ListingForm({
  mode,
  property,
  onSuccess,
}: {
  mode: 'create' | 'edit';
  property?: PropertyDetail;
  onSuccess?: (property: PropertyDetail) => void;
}) {
  const createListing = useCreateListing();
  const updateListing = useUpdateListing();
  const { data: categories, isLoading: categoriesLoading } = usePropertyCategories();

  const initialCategoryId = resolveCategoryId(property);
  const initialAttributes = useMemo(() => buildAttributeState(property), [property]);
  const initialBlocks = useMemo(() => buildAvailabilityBlocks(property), [property]);

  const [attributeValues, setAttributeValues] = useState<Record<string, AttributeFormValue>>(initialAttributes);
  const [availabilityBlocks, setAvailabilityBlocks] = useState<AvailabilityBlockInput[]>(initialBlocks);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<ListingFormInput, unknown, ListingFormValues>({
    resolver: zodResolver(listingSchema),
    defaultValues: {
      category_id: initialCategoryId,
      name: property?.name ?? '',
      description: property?.description ?? '',
      location_address: property?.location_address ?? '',
      location_lat: property?.location_lat ?? undefined,
      location_lng: property?.location_lng ?? undefined,
      deposit_amount: property?.deposit_amount ?? 0,
      min_rental_duration_hours: property?.min_rental_duration_hours ?? 24,
      max_rental_duration_days: property?.max_rental_duration_days ?? 365,
      booking_lead_time_hours: property?.booking_lead_time_hours ?? 0,
      instant_booking_enabled: property?.instant_booking_enabled ?? false,
    },
  });

  const categoryId = useWatch({ control, name: 'category_id' });
  const { data: categoryDetail, isLoading: categoryDetailLoading } = usePropertyCategory(categoryId);

  useEffect(() => {
    setAttributeValues(initialAttributes);
  }, [initialAttributes]);

  useEffect(() => {
    setAvailabilityBlocks(initialBlocks);
  }, [initialBlocks]);

  const isSaving = createListing.isPending || updateListing.isPending;

  const submit = async (values: ListingFormValues) => {
    setFormError(null);
    setFormSuccess(null);

    const requiredAttributes = (categoryDetail?.attributes ?? []).filter(
      (attribute) => attribute.is_required && isAttributeEmpty(attributeValues[attribute.id])
    );

    if (requiredAttributes.length > 0) {
      setFormError(
        `Add the required property details before saving: ${requiredAttributes
          .map((attribute) => attribute.name)
          .join(', ')}.`
      );
      return;
    }

    const attributePayload = (categoryDetail?.attributes ?? [])
      .map((attribute) => ({
        attribute_id: attribute.id,
        value: serializeAttributeValue(attribute, attributeValues[attribute.id]),
      }))
      .filter((attribute) => attribute.value !== null);

    const blockPayload = availabilityBlocks
      .filter((block) => block.start_at && block.end_at)
      .map((block) => ({
        ...block,
        start_at: toIsoDateTime(block.start_at) ?? block.start_at,
        end_at: toIsoDateTime(block.end_at) ?? block.end_at,
        reason: block.reason?.trim() || null,
      }));

    const payload: PropertyMutationPayload = {
      category_id: values.category_id,
      name: values.name.trim(),
      description: values.description.trim(),
      location_address: values.location_address.trim(),
      location_lat: values.location_lat ?? null,
      location_lng: values.location_lng ?? null,
      deposit_amount: values.deposit_amount,
      min_rental_duration_hours: values.min_rental_duration_hours,
      max_rental_duration_days: values.max_rental_duration_days,
      booking_lead_time_hours: values.booking_lead_time_hours,
      instant_booking_enabled: values.instant_booking_enabled,
      attribute_values: attributePayload,
      availability_blocks: blockPayload,
    };

    try {
      const saved =
        mode === 'edit' && property
          ? await updateListing.mutateAsync({ propertyId: property.id, data: payload })
          : await createListing.mutateAsync(payload);

      setFormSuccess(
        mode === 'edit'
          ? 'Listing details saved. Pricing rules and media stay editable below.'
          : 'Draft created. Continue below to add pricing rules and photos.'
      );
      onSuccess?.(saved);
    } catch {
      setFormError('Unable to save the listing right now. Please review the form and try again.');
    }
  };

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Home className="h-5 w-5 text-blue-600" />
            {mode === 'edit' ? 'Listing details' : 'Create draft listing'}
          </CardTitle>
          <CardDescription>
            Capture the essentials first, then layer in pricing, photos, and availability controls.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Property type</label>
            <select
              {...register('category_id')}
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a property type</option>
              {(categories ?? []).map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            {categoriesLoading ? (
              <p className="mt-1 text-xs text-gray-400">Loading property types…</p>
            ) : null}
            {errors.category_id?.message ? (
              <p className="mt-1 text-sm text-red-600">{errors.category_id.message}</p>
            ) : null}
          </div>

          <Input
            label="Listing name"
            {...register('name')}
            error={errors.name?.message}
            placeholder="Sunny two-bedroom apartment"
          />

          <div className="md:col-span-2">
            <label className="mb-1 block text-sm font-medium text-gray-700">Description</label>
            <textarea
              {...register('description')}
              rows={5}
              placeholder="Describe the neighbourhood, floor plan, standout amenities, and what tenants can expect."
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.description?.message ? (
              <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
            ) : null}
          </div>

          <div className="md:col-span-2">
            <Input
              label="Address"
              {...register('location_address')}
              error={errors.location_address?.message}
              placeholder="Jhamsikhel, Lalitpur"
            />
          </div>

          <Input
            label="Latitude"
            type="number"
            step="0.000001"
            {...register('location_lat')}
            error={errors.location_lat?.message}
            placeholder="27.6810"
          />
          <Input
            label="Longitude"
            type="number"
            step="0.000001"
            {...register('location_lng')}
            error={errors.location_lng?.message}
            placeholder="85.3188"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Rental controls</CardTitle>
          <CardDescription>
            These values drive quote generation and availability validation for renters.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Input
            label="Security deposit"
            type="number"
            min="0"
            step="0.01"
            {...register('deposit_amount')}
            error={errors.deposit_amount?.message}
          />
          <Input
            label="Minimum rental duration (hours)"
            type="number"
            min="1"
            step="1"
            {...register('min_rental_duration_hours')}
            error={errors.min_rental_duration_hours?.message}
          />
          <Input
            label="Maximum rental duration (days)"
            type="number"
            min="1"
            step="1"
            {...register('max_rental_duration_days')}
            error={errors.max_rental_duration_days?.message}
          />
          <Input
            label="Lead time before booking (hours)"
            type="number"
            min="0"
            step="1"
            {...register('booking_lead_time_hours')}
            error={errors.booking_lead_time_hours?.message}
          />

          <div className="md:col-span-2 xl:col-span-4">
            <label className="flex items-center gap-3 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-700">
              <input
                type="checkbox"
                {...register('instant_booking_enabled')}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              Enable instant booking once pricing and availability are ready
            </label>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">Category-specific details</CardTitle>
          <CardDescription>
            Capture amenities and filters defined by the selected property type.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!categoryId ? (
            <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center text-sm text-gray-500">
              Choose a property type to reveal its extra attributes.
            </div>
          ) : categoryDetailLoading ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-24 w-full rounded-lg md:col-span-2" />
            </div>
          ) : categoryDetail?.attributes.length ? (
            <div className="grid gap-4 md:grid-cols-2">
              {categoryDetail.attributes.map((attribute) => (
                <AttributeField
                  key={attribute.id}
                  attribute={attribute}
                  value={attributeValues[attribute.id]}
                  onChange={(value) =>
                    setAttributeValues((current) => ({ ...current, [attribute.id]: value }))
                  }
                />
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center text-sm text-gray-500">
              This property type does not define extra attributes yet.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <CalendarMinus className="h-5 w-5 text-blue-600" />
            Manual availability blocks
          </CardTitle>
          <CardDescription>
            Reserve blackout windows for owner stays or maintenance until dedicated availability tooling arrives.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {availabilityBlocks.length > 0 ? (
            availabilityBlocks.map((block, index) => (
              <div
                key={block.id ?? `${block.start_at}-${block.end_at}-${index}`}
                className="grid gap-4 rounded-2xl border border-gray-200 p-4 lg:grid-cols-[180px,1fr,1fr,1fr,auto]"
              >
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Block type</label>
                  <select
                    value={block.block_type}
                    onChange={(event) =>
                      setAvailabilityBlocks((current) =>
                        current.map((item, currentIndex) =>
                          currentIndex === index ? { ...item, block_type: event.target.value } : item
                        )
                      )
                    }
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {MANUAL_BLOCK_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                <Input
                  label="Start"
                  type="datetime-local"
                  value={block.start_at}
                  onChange={(event) =>
                    setAvailabilityBlocks((current) =>
                      current.map((item, currentIndex) =>
                        currentIndex === index ? { ...item, start_at: event.target.value } : item
                      )
                    )
                  }
                />
                <Input
                  label="End"
                  type="datetime-local"
                  value={block.end_at}
                  onChange={(event) =>
                    setAvailabilityBlocks((current) =>
                      current.map((item, currentIndex) =>
                        currentIndex === index ? { ...item, end_at: event.target.value } : item
                      )
                    )
                  }
                />
                <Input
                  label="Reason"
                  value={block.reason ?? ''}
                  onChange={(event) =>
                    setAvailabilityBlocks((current) =>
                      current.map((item, currentIndex) =>
                        currentIndex === index ? { ...item, reason: event.target.value } : item
                      )
                    )
                  }
                  placeholder="Owner visit, repainting, deep cleaning"
                />

                <div className="flex items-end">
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() =>
                      setAvailabilityBlocks((current) =>
                        current.filter((_, currentIndex) => currentIndex !== index)
                      )
                    }
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center text-sm text-gray-500">
              No blackout windows yet. Add one if you already know about planned downtime.
            </div>
          )}

          <Button
            type="button"
            variant="outline"
            onClick={() => setAvailabilityBlocks((current) => [...current, emptyAvailabilityBlock()])}
          >
            <Plus className="mr-2 h-4 w-4" />
            Add availability block
          </Button>
        </CardContent>
      </Card>

      {formError ? (
        <div className="flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{formError}</span>
        </div>
      ) : null}

      {formSuccess ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {formSuccess}
        </div>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <Button type="submit" isLoading={isSaving}>
          {mode === 'edit' ? 'Save listing changes' : 'Create draft listing'}
        </Button>
        {mode === 'create' ? (
          <p className="self-center text-sm text-gray-500">
            You can upload media and configure pricing as soon as the draft is created.
          </p>
        ) : null}
      </div>
    </form>
  );
}
