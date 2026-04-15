import type { ReactNode } from 'react';
import { ExternalLink, FileSignature } from 'lucide-react';
import { Skeleton } from '@/components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { formatBookingDateTime } from '@/lib/bookings';
import type { RentalAgreement } from '@/types';
import { BookingStatusBadge } from './booking-status-badge';

interface AgreementSummaryCardProps {
  agreement?: RentalAgreement | null;
  isLoading?: boolean;
  actions?: ReactNode;
}

export function AgreementSummaryCard({
  agreement,
  isLoading,
  actions,
}: AgreementSummaryCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <FileSignature className="h-5 w-5 text-blue-600" />
          Lease agreement
        </CardTitle>
        <CardDescription>
          Generated clauses, signature state, and document handoff for this booking.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <Skeleton className="h-44 w-full rounded-2xl" />
        ) : agreement ? (
          <div className="space-y-4">
            <div className="flex flex-wrap items-start justify-between gap-3 rounded-2xl border border-gray-200 bg-gray-50 p-4">
              <div>
                <p className="text-sm font-semibold text-gray-900">{agreement.template.name}</p>
                <p className="mt-1 text-sm text-gray-500">
                  Template v{agreement.template.version} · Agreement v{agreement.version}
                </p>
              </div>
              <BookingStatusBadge kind="agreement" status={agreement.status} />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-gray-200 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                  Sent to signer
                </p>
                <p className="mt-1 text-sm font-medium text-gray-900">
                  {formatBookingDateTime(agreement.sent_at)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                  Tenant signature
                </p>
                <p className="mt-1 text-sm font-medium text-gray-900">
                  {formatBookingDateTime(agreement.customer_signed_at)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                  Owner signature
                </p>
                <p className="mt-1 text-sm font-medium text-gray-900">
                  {formatBookingDateTime(agreement.owner_signed_at)}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-200 px-4 py-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                  Signature request
                </p>
                <p className="mt-1 text-sm font-medium text-gray-900">
                  {agreement.esign_request_id ?? 'Not sent yet'}
                </p>
              </div>
            </div>

            {(agreement.rendered_document_url || agreement.signed_document_url) ? (
              <div className="flex flex-wrap gap-2">
                {agreement.rendered_document_url ? (
                  <a
                    href={agreement.rendered_document_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    View draft document
                    <ExternalLink className="h-4 w-4" />
                  </a>
                ) : null}
                {agreement.signed_document_url ? (
                  <a
                    href={agreement.signed_document_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    View signed document
                    <ExternalLink className="h-4 w-4" />
                  </a>
                ) : null}
              </div>
            ) : null}

            {agreement.custom_clauses.length ? (
              <div className="rounded-2xl border border-gray-200 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                  Custom clauses
                </p>
                <ul className="mt-3 space-y-2 text-sm text-gray-600">
                  {agreement.custom_clauses.map((clause) => (
                    <li key={clause} className="rounded-xl bg-gray-50 px-3 py-2">
                      {clause}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {agreement.rendered_content ? (
              <div className="rounded-2xl border border-gray-200 px-4 py-4">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                  Rendered content preview
                </p>
                <div className="mt-3 max-h-56 overflow-auto whitespace-pre-wrap rounded-xl bg-gray-50 p-3 text-sm text-gray-600">
                  {agreement.rendered_content}
                </div>
              </div>
            ) : null}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center text-sm text-gray-500">
            No generated agreement yet. Create a draft after the booking is approved.
          </div>
        )}

        {actions ? <div className="border-t border-gray-200 pt-4">{actions}</div> : null}
      </CardContent>
    </Card>
  );
}
