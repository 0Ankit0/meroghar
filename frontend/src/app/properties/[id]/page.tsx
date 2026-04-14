'use client';

import { use, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  ArrowLeft,
  CalendarDays,
  Clock3,
  MapPin,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { Button, Input, Skeleton } from '@/components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useProperty, usePropertyAvailability, usePropertyPriceQuote } from '@/hooks/use-properties';
import {
  formatAvailabilityBlockType,
  formatDateRange,
  formatMoney,
  formatPropertyStatus,
  formatRateType,
  getPropertyCoverPhoto,
  propertyStatusTone,
  toDateTimeLocalValue,
} from '@/lib/properties';

function createLocalDateOffset(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return toDateTimeLocalValue(date.toISOString());
}

function renderValue(value: unknown) {
  if (Array.isArray(value)) return value.join(', ');
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  return value === null || value === undefined ? '—' : String(value);
}

export default function PropertyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const searchParams = useSearchParams();

  const initialStart = toDateTimeLocalValue(searchParams.get('start')) || searchParams.get('start') || '';
  const initialEnd = toDateTimeLocalValue(searchParams.get('end')) || searchParams.get('end') || '';

  const [quoteWindow, setQuoteWindow] = useState({
    start: initialStart,
    end: initialEnd,
  });

  const { data: property, isLoading, error } = useProperty(id);

  const availabilityWindow = useMemo(
    () => ({
      start: quoteWindow.start || createLocalDateOffset(0),
      end: quoteWindow.end || createLocalDateOffset(30),
    }),
    [quoteWindow]
  );

  const { data: availability, isLoading: availabilityLoading } = usePropertyAvailability(id, availabilityWindow);
  const { data: quote, isLoading: quoteLoading } = usePropertyPriceQuote(
    id,
    quoteWindow.start && quoteWindow.end ? quoteWindow : undefined
  );

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 sm:px-6 lg:px-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-[380px] w-full rounded-3xl" />
        <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
          <Skeleton className="h-[420px] w-full rounded-3xl" />
          <Skeleton className="h-[420px] w-full rounded-3xl" />
        </div>
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="mx-auto flex min-h-[70vh] max-w-3xl flex-col items-center justify-center gap-4 px-4 text-center">
        <ShieldCheck className="h-12 w-12 text-gray-300" />
        <h1 className="text-2xl font-semibold text-gray-900">Property not found</h1>
        <p className="text-gray-500">The listing may have been archived or is no longer published.</p>
        <Link href="/properties">
          <Button variant="outline">Back to search</Button>
        </Link>
      </div>
    );
  }

  const coverPhoto = getPropertyCoverPhoto(property);
  const galleryPhotos = property.photos?.slice(1, 5) ?? [];
  const blocks = availability?.blocks ?? property.availability_blocks ?? [];

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link href="/properties" className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700">
            <ArrowLeft className="h-4 w-4" />
            Back to properties
          </Link>
          <span
            className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${propertyStatusTone(property.status, property.is_published)}`}
          >
            {formatPropertyStatus(property.status, property.is_published)}
          </span>
        </div>

        <section className="space-y-6">
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-600">
              {property.category?.name ?? 'Property'}
            </p>
            <h1 className="text-4xl font-bold tracking-tight text-gray-900">{property.name}</h1>
            {property.location_address ? (
              <div className="flex items-center gap-2 text-base text-gray-600">
                <MapPin className="h-4 w-4 text-gray-400" />
                <span>{property.location_address}</span>
              </div>
            ) : null}
            {property.description ? (
              <p className="max-w-4xl text-lg leading-8 text-gray-600">{property.description}</p>
            ) : null}
          </div>

          <div className="grid gap-4 lg:grid-cols-[2fr,1fr]">
            <div className="overflow-hidden rounded-3xl border border-gray-200 bg-white">
              <div className="aspect-[16/10] bg-gray-100">
                {coverPhoto ? (
                  <img src={coverPhoto.url} alt={property.name} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
                    <ShieldCheck className="h-16 w-16 text-blue-300" />
                  </div>
                )}
              </div>
            </div>
            <div className="grid gap-4">
              {galleryPhotos.length ? (
                galleryPhotos.map((photo) => (
                  <div key={photo.id} className="overflow-hidden rounded-3xl border border-gray-200 bg-white">
                    <div className="aspect-[4/3] bg-gray-100">
                      <img src={photo.url} alt={photo.caption ?? property.name} className="h-full w-full object-cover" />
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex h-full min-h-[240px] items-center justify-center rounded-3xl border border-dashed border-gray-300 bg-white p-6 text-center text-sm text-gray-500">
                  Add photos from the landlord workspace to enrich this listing.
                </div>
              )}
            </div>
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Features and amenity summary</CardTitle>
                <CardDescription>
                  Category-specific attributes shown to renters during discovery.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {property.attributes?.length ? (
                  <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                    {property.attributes.map((attribute) => (
                      <div
                        key={`${property.id}-${attribute.attribute_id}`}
                        className="rounded-2xl border border-gray-200 bg-gray-50 px-4 py-3"
                      >
                        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                          {attribute.attribute_name ?? attribute.attribute_slug ?? 'Feature'}
                        </p>
                        <p className="mt-1 text-sm font-medium text-gray-900">
                          {renderValue(attribute.value)}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    This listing does not expose extra category attributes yet.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Availability preview</CardTitle>
                <CardDescription>
                  Current blocked dates returned by the availability endpoint for the selected window.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {availabilityLoading ? (
                  <Skeleton className="h-28 w-full rounded-2xl" />
                ) : blocks.length ? (
                  blocks.map((block) => (
                    <div key={block.id} className="rounded-2xl border border-gray-200 px-4 py-3">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            {formatAvailabilityBlockType(block.block_type)}
                          </p>
                          <p className="mt-1 text-sm text-gray-500">
                            {formatDateRange(block.start_at, block.end_at)}
                          </p>
                        </div>
                        {block.reason ? (
                          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-600">
                            {block.reason}
                          </span>
                        ) : null}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center text-sm text-gray-500">
                    No blocked dates were returned for this window.
                  </div>
                )}

                {availability?.next_available_start ? (
                  <p className="text-sm text-blue-700">
                    Next available from {formatDateRange(availability.next_available_start, availability.next_available_start)}.
                  </p>
                ) : null}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Sparkles className="h-5 w-5 text-blue-600" />
                  Quote this stay
                </CardTitle>
                <CardDescription>
                  Pricing quotes use the documented price endpoint and include deposit totals.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  label="Move-in"
                  type="datetime-local"
                  value={quoteWindow.start}
                  onChange={(event) =>
                    setQuoteWindow((current) => ({ ...current, start: event.target.value }))
                  }
                />
                <Input
                  label="Move-out"
                  type="datetime-local"
                  value={quoteWindow.end}
                  onChange={(event) =>
                    setQuoteWindow((current) => ({ ...current, end: event.target.value }))
                  }
                />

                {quoteLoading ? (
                  <Skeleton className="h-40 w-full rounded-2xl" />
                ) : quote ? (
                  <div className="space-y-3 rounded-2xl border border-gray-200 bg-gray-50 p-4">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Rate basis</span>
                      <span className="font-medium text-gray-900">{formatRateType(quote.rate_type)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Base fee</span>
                      <span className="font-medium text-gray-900">{formatMoney(quote.base_fee, quote.currency)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Peak surcharge</span>
                      <span className="font-medium text-gray-900">
                        {formatMoney(quote.peak_surcharge ?? 0, quote.currency)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Discount</span>
                      <span className="font-medium text-gray-900">
                        {formatMoney(quote.discount_amount ?? 0, quote.currency)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Tax</span>
                      <span className="font-medium text-gray-900">{formatMoney(quote.tax_amount ?? 0, quote.currency)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Deposit</span>
                      <span className="font-medium text-gray-900">
                        {formatMoney(quote.deposit_amount ?? property.deposit_amount ?? 0, quote.currency)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between border-t border-gray-200 pt-3">
                      <span className="text-sm font-semibold text-gray-700">Total due now</span>
                      <span className="text-xl font-semibold text-gray-900">
                        {formatMoney(quote.total_due, quote.currency)}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="rounded-2xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500">
                    Pick a move-in and move-out window to request a price breakdown.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-xl">Stay policies</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 text-sm text-gray-600">
                    <Clock3 className="h-4 w-4 text-blue-500" />
                    Minimum rental duration
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {property.min_rental_duration_hours ? `${property.min_rental_duration_hours}h` : 'Flexible'}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 text-sm text-gray-600">
                    <CalendarDays className="h-4 w-4 text-blue-500" />
                    Maximum rental duration
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {property.max_rental_duration_days ? `${property.max_rental_duration_days} days` : 'Flexible'}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 text-sm text-gray-600">
                    <ShieldCheck className="h-4 w-4 text-blue-500" />
                    Booking lead time
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {property.booking_lead_time_hours ? `${property.booking_lead_time_hours}h` : 'No lead time'}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 text-sm text-gray-600">
                    <Sparkles className="h-4 w-4 text-blue-500" />
                    Instant booking
                  </div>
                  <span className="text-sm font-medium text-gray-900">
                    {property.instant_booking_enabled ? 'Enabled' : 'Manual approval'}
                  </span>
                </div>
                <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
                  Rental applications ship in the next slice. This page focuses on discovery, pricing,
                  and availability.
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
