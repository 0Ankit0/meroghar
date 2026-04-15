'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, FileSignature } from 'lucide-react';
import { Button, Skeleton } from '@/components/ui';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BookingStatusBadge } from '@/components/bookings/booking-status-badge';
import { useBookings } from '@/hooks/use-bookings';
import {
  formatBookingWindow,
  hasBookingManagementAccess,
  hasBookingViewAccess,
} from '@/lib/bookings';
import { formatMoney } from '@/lib/properties';
import { useAuthStore } from '@/store/auth-store';

const statusOptions = [
  { label: 'All statuses', value: 'all' },
  { label: 'Pending', value: 'pending' },
  { label: 'Confirmed', value: 'confirmed' },
  { label: 'Active', value: 'active' },
  { label: 'Pending closure', value: 'pending_closure' },
  { label: 'Closed', value: 'closed' },
  { label: 'Cancelled', value: 'cancelled' },
  { label: 'Declined', value: 'declined' },
];

function parsePage(value: string | null) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

export default function BookingsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const page = parsePage(searchParams.get('page'));
  const status = searchParams.get('status') ?? 'all';

  const user = useAuthStore((state) => state.user);
  const canViewBookings = hasBookingViewAccess(user?.roles, user?.is_superuser);
  const canManageBookings = hasBookingManagementAccess(user?.roles, user?.is_superuser);
  const { data, isLoading, error } = useBookings({
    page,
    per_page: 20,
    status,
  });

  const bookings = data?.items ?? [];
  const pendingCount = bookings.filter((booking) => booking.status === 'pending').length;
  const activeCount = bookings.filter((booking) =>
    ['confirmed', 'active', 'pending_closure'].includes(booking.status)
  ).length;
  const agreementCount = bookings.filter((booking) =>
    booking.agreement_status && !['signed', 'terminated'].includes(booking.agreement_status)
  ).length;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / Math.max(data.per_page, 1))) : 1;

  const updateFilters = (next: { page?: number; status?: string }) => {
    const params = new URLSearchParams(searchParams.toString());

    if (next.page && next.page > 1) {
      params.set('page', String(next.page));
    } else {
      params.delete('page');
    }

    if (next.status && next.status !== 'all') {
      params.set('status', next.status);
    } else {
      params.delete('status');
    }

    router.push(params.toString() ? `/bookings?${params.toString()}` : '/bookings');
  };

  if (!canViewBookings) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 px-6 py-5 text-sm text-amber-700">
        This workspace does not expose booking workflows for your role.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bookings</h1>
          <p className="text-gray-500">
            {canManageBookings
              ? 'Approve tenant requests, generate agreements, and close return workflows.'
              : 'Track your requests, stay status, and lease-signing progress.'}
          </p>
        </div>
        {!canManageBookings ? (
          <Link href="/properties">
            <Button>Browse properties</Button>
          </Link>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-gray-200 bg-white px-4 py-4">
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { label: 'Bookings on this page', value: bookings.length },
            { label: 'Pending approval', value: pendingCount },
            { label: 'Lease in progress', value: agreementCount },
            { label: 'Active or confirmed', value: activeCount },
          ].map((metric) => (
            <div key={metric.label}>
              <p className="text-sm text-gray-500">{metric.label}</p>
              <p className="mt-1 text-2xl font-semibold text-gray-900">{metric.value}</p>
            </div>
          ))}
        </div>

        <div className="w-full max-w-xs">
          <label htmlFor="booking-status-filter" className="mb-1 block text-sm font-medium text-gray-700">
            Filter by status
          </label>
          <select
            id="booking-status-filter"
            value={status}
            onChange={(event) => updateFilters({ status: event.target.value, page: 1 })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-xl">Booking queue</CardTitle>
          {data ? <span className="text-sm text-gray-500">Total returned: {data.total}</span> : null}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((key) => (
                <Skeleton key={key} className="h-20 w-full rounded-xl" />
              ))}
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-6 text-sm text-red-700">
              Unable to load bookings right now.
            </div>
          ) : bookings.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[980px]">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Booking</th>
                    <th className="pb-3 font-medium">Property</th>
                    <th className="pb-3 font-medium">Stay window</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Agreement</th>
                    <th className="pb-3 font-medium">Due now</th>
                    <th className="pb-3 font-medium">Updated</th>
                    <th className="pb-3 text-right font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {bookings.map((booking) => (
                    <tr key={booking.id} className="border-b border-gray-100 align-top last:border-0">
                      <td className="py-4">
                        <div>
                          <p className="font-medium text-gray-900">{booking.booking_number}</p>
                          <p className="mt-1 text-sm text-gray-500">{booking.id}</p>
                        </div>
                      </td>
                      <td className="py-4">
                        <div>
                          <p className="font-medium text-gray-900">{booking.property.name}</p>
                          <p className="mt-1 text-sm text-gray-500">
                            {booking.property.location_address ?? '—'}
                          </p>
                        </div>
                      </td>
                      <td className="py-4 text-sm text-gray-600">
                        {formatBookingWindow(booking.rental_start_at, booking.rental_end_at)}
                      </td>
                      <td className="py-4">
                        <BookingStatusBadge status={booking.status} />
                      </td>
                      <td className="py-4">
                        {booking.agreement_status ? (
                          <BookingStatusBadge kind="agreement" status={booking.agreement_status} />
                        ) : (
                          <span className="text-sm text-gray-500">Not started</span>
                        )}
                      </td>
                      <td className="py-4 text-sm font-medium text-gray-900">
                        {formatMoney(booking.pricing.total_due_now, booking.pricing.currency)}
                      </td>
                      <td className="py-4 text-sm text-gray-600">
                        {booking.updated_at ? new Date(booking.updated_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="py-4">
                        <div className="flex justify-end">
                          <Link href={`/bookings/${booking.id}`}>
                            <Button variant="outline" size="sm">
                              <FileSignature className="mr-2 h-4 w-4" />
                              View workflow
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-16 text-center">
              <p className="text-lg font-medium text-gray-900">No bookings yet</p>
              <p className="mt-2 text-sm text-gray-500">
                {canManageBookings
                  ? 'Tenant requests will appear here once applications start arriving.'
                  : 'Your submitted requests will appear here after you book a property.'}
              </p>
              <Link href={canManageBookings ? '/listings' : '/properties'} className="mt-6 inline-flex">
                <Button variant="outline">
                  {canManageBookings ? 'Review listings' : 'Browse properties'}
                </Button>
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 ? (
        <div className="flex items-center justify-between rounded-2xl border border-gray-200 bg-white px-4 py-3">
          <Button variant="outline" onClick={() => updateFilters({ page: page - 1, status })} disabled={page <= 1}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>
          <span className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            onClick={() => updateFilters({ page: page + 1, status })}
            disabled={page >= totalPages}
          >
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      ) : null}
    </div>
  );
}
