import Link from 'next/link';
import { BedDouble, CalendarDays, MapPin, ShieldCheck, Star } from 'lucide-react';
import { Card } from '@/components/ui/card';
import {
  formatMoney,
  formatPropertyStatus,
  formatRateType,
  getPropertyCoverPhoto,
  propertyStatusTone,
} from '@/lib/properties';
import type { PropertyAttributeValue, PropertySummary } from '@/types';

function valueLabel(value: PropertyAttributeValue['value']) {
  if (Array.isArray(value)) {
    return value.join(', ');
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  return value === null || value === undefined ? null : String(value);
}

export function PropertyCard({ property, href }: { property: PropertySummary; href: string }) {
  const coverPhoto = getPropertyCoverPhoto(property);
  const attributeHighlights = (property.attributes ?? []).filter((attribute) => valueLabel(attribute.value)).slice(0, 3);
  const pricingPreview = property.pricing_preview;
  const priceLabel =
    pricingPreview && pricingPreview.total_due > 0
      ? `${formatRateType(pricingPreview.rate_type)} estimate`
      : 'Security deposit';
  const priceValue =
    pricingPreview && pricingPreview.total_due > 0
      ? formatMoney(pricingPreview.total_due, pricingPreview.currency)
      : formatMoney(property.deposit_amount ?? 0);

  return (
    <Card className="overflow-hidden transition-shadow hover:shadow-lg">
      <Link href={href} className="block">
        <div className="relative aspect-[16/10] bg-gray-100">
          {coverPhoto ? (
            <img src={coverPhoto.url} alt={property.name} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
              <ShieldCheck className="h-12 w-12 text-blue-300" />
            </div>
          )}
          <div className="absolute right-4 top-4">
            <span
              className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${propertyStatusTone(property.status, property.is_published)}`}
            >
              {formatPropertyStatus(property.status, property.is_published)}
            </span>
          </div>
        </div>

        <div className="space-y-4 p-5">
          <div className="space-y-2">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-blue-600">
                  {property.category?.name ?? 'Property'}
                </p>
                <h3 className="text-xl font-semibold text-gray-900">{property.name}</h3>
              </div>
              {property.average_rating ? (
                <div className="flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
                  <Star className="h-3.5 w-3.5 fill-current" />
                  {property.average_rating.toFixed(1)}
                </div>
              ) : null}
            </div>

            {property.location_address ? (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <MapPin className="h-4 w-4 text-gray-400" />
                <span>{property.location_address}</span>
              </div>
            ) : null}

            {property.description ? (
              <p className="line-clamp-3 text-sm leading-6 text-gray-600">{property.description}</p>
            ) : null}
          </div>

          <div className="rounded-xl bg-gray-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-gray-400">{priceLabel}</p>
            <p className="mt-1 text-2xl font-semibold text-gray-900">{priceValue}</p>
            {pricingPreview?.deposit_amount ? (
              <p className="mt-1 text-sm text-gray-500">
                Deposit {formatMoney(pricingPreview.deposit_amount, pricingPreview.currency)}
              </p>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-2 text-xs text-gray-600">
            {property.min_rental_duration_hours ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 shadow-sm ring-1 ring-gray-200">
                <CalendarDays className="h-3.5 w-3.5 text-blue-500" />
                Min {property.min_rental_duration_hours}h
              </span>
            ) : null}
            {property.max_rental_duration_days ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 shadow-sm ring-1 ring-gray-200">
                <BedDouble className="h-3.5 w-3.5 text-blue-500" />
                Max {property.max_rental_duration_days} days
              </span>
            ) : null}
            {property.instant_booking_enabled ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-3 py-1 font-medium text-emerald-700 ring-1 ring-emerald-200">
                Instant booking
              </span>
            ) : null}
          </div>

          {attributeHighlights.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {attributeHighlights.map((attribute) => (
                <span
                  key={`${property.id}-${attribute.attribute_id}`}
                  className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700"
                >
                  {(attribute.attribute_name ?? attribute.attribute_slug ?? 'Feature')}: {valueLabel(attribute.value)}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      </Link>
    </Card>
  );
}
