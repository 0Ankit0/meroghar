'use client';

import { use, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, CalendarDays, Eye } from 'lucide-react';
import { ListingForm } from '@/components/listings/listing-form';
import { PhotoManager } from '@/components/listings/photo-manager';
import { PricingRulesEditor } from '@/components/listings/pricing-rules-editor';
import { Button, Input, Skeleton } from '@/components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useProperty, usePropertyAvailability } from '@/hooks/use-properties';
import {
  formatAvailabilityBlockType,
  formatDateRange,
  formatPropertyStatus,
  propertyStatusTone,
  toDateTimeLocalValue,
} from '@/lib/properties';

function createLocalDateOffset(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return toDateTimeLocalValue(date.toISOString());
}

export default function EditListingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const searchParams = useSearchParams();
  const showCreatedNotice = searchParams.get('created') === '1';

  const { data: property, isLoading, error } = useProperty(id);

  const [availabilityWindow, setAvailabilityWindow] = useState({
    start: createLocalDateOffset(0),
    end: createLocalDateOffset(60),
  });

  const { data: availability, isLoading: availabilityLoading } = usePropertyAvailability(id, availabilityWindow);
  const availabilityBlocks = useMemo(() => availability?.blocks ?? [], [availability]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-[720px] w-full rounded-3xl" />
      </div>
    );
  }

  if (error || !property) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-6 text-sm text-red-700">
        Unable to load this listing. It may have been archived or your session may not have access.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-3">
          <Link href="/listings" className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700">
            <ArrowLeft className="h-4 w-4" />
            Back to listings
          </Link>
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{property.name}</h1>
              <span
                className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${propertyStatusTone(property.status, property.is_published)}`}
              >
                {formatPropertyStatus(property.status, property.is_published)}
              </span>
            </div>
            <p className="text-gray-500">
              Update the listing details, then manage pricing, media, and published availability below.
            </p>
          </div>
        </div>

        <Link href={`/properties/${property.id}`}>
          <Button variant="outline">
            <Eye className="mr-2 h-4 w-4" />
            Public preview
          </Button>
        </Link>
      </div>

      {showCreatedNotice ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          Draft created successfully. Continue configuring pricing rules and photos before publishing.
        </div>
      ) : null}

      <ListingForm mode="edit" property={property} />

      <PhotoManager propertyId={property.id} photos={property.photos ?? []} />

      <PricingRulesEditor propertyId={property.id} />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <CalendarDays className="h-5 w-5 text-blue-600" />
            Availability endpoint preview
          </CardTitle>
          <CardDescription>
            Use the public availability feed to verify blackout windows that renters will see.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="Preview start"
              type="datetime-local"
              value={availabilityWindow.start}
              onChange={(event) =>
                setAvailabilityWindow((current) => ({ ...current, start: event.target.value }))
              }
            />
            <Input
              label="Preview end"
              type="datetime-local"
              value={availabilityWindow.end}
              onChange={(event) =>
                setAvailabilityWindow((current) => ({ ...current, end: event.target.value }))
              }
            />
          </div>

          {availabilityLoading ? (
            <Skeleton className="h-32 w-full rounded-2xl" />
          ) : availabilityBlocks.length ? (
            availabilityBlocks.map((block) => (
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
              No blocked dates returned for this window.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
