'use client';

import { use, useMemo, useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FileSignature,
  MapPin,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { Button, Input, Skeleton } from '@/components/ui';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AgreementSummaryCard } from '@/components/bookings/agreement-summary-card';
import { BookingStatusBadge } from '@/components/bookings/booking-status-badge';
import { BookingTimeline } from '@/components/bookings/booking-timeline';
import {
  useBooking,
  useBookingAgreement,
  useBookingEvents,
  useCancelBooking,
  useConfirmBooking,
  useCountersignAgreement,
  useDeclineBooking,
  useGenerateAgreement,
  useReturnBooking,
  useSendAgreement,
} from '@/hooks/use-bookings';
import {
  formatBookingDateTime,
  formatBookingWindow,
  hasBookingManagementAccess,
  hasBookingViewAccess,
} from '@/lib/bookings';
import { formatMoney } from '@/lib/properties';
import { useAuthStore } from '@/store/auth-store';

function splitClauses(value: string): string[] {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function BookingDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const user = useAuthStore((state) => state.user);
  const canViewBookings = hasBookingViewAccess(user?.roles, user?.is_superuser);
  const canManageBookings = hasBookingManagementAccess(user?.roles, user?.is_superuser);

  const { data: booking, isLoading, error } = useBooking(id);
  const { data: events = [] } = useBookingEvents(id);
  const { data: agreement, isLoading: agreementLoading } = useBookingAgreement(id);

  const confirmBooking = useConfirmBooking();
  const declineBooking = useDeclineBooking();
  const cancelBooking = useCancelBooking();
  const returnBooking = useReturnBooking();
  const generateAgreement = useGenerateAgreement();
  const sendAgreement = useSendAgreement();
  const countersignAgreement = useCountersignAgreement();

  const [declineReason, setDeclineReason] = useState('');
  const [cancelReason, setCancelReason] = useState('');
  const [returnAt, setReturnAt] = useState('');
  const [returnNotes, setReturnNotes] = useState('');
  const [customClauses, setCustomClauses] = useState('');

  const actionError = useMemo(() => {
    const errorSource =
      confirmBooking.error ??
      declineBooking.error ??
      cancelBooking.error ??
      returnBooking.error ??
      generateAgreement.error ??
      sendAgreement.error ??
      countersignAgreement.error;

    if (!errorSource) {
      return null;
    }

    return errorSource instanceof Error
      ? errorSource.message
      : 'Unable to complete that booking action right now.';
  }, [
    cancelBooking.error,
    confirmBooking.error,
    countersignAgreement.error,
    declineBooking.error,
    generateAgreement.error,
    returnBooking.error,
    sendAgreement.error,
  ]);

  if (!canViewBookings) {
    return (
      <div className="rounded-2xl border border-amber-200 bg-amber-50 px-6 py-5 text-sm text-amber-700">
        This workspace does not expose booking workflows for your role.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-44 w-full rounded-2xl" />
        <div className="grid gap-6 lg:grid-cols-[1.3fr,0.9fr]">
          <Skeleton className="h-[420px] w-full rounded-2xl" />
          <Skeleton className="h-[420px] w-full rounded-2xl" />
        </div>
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 px-6 py-5 text-sm text-red-700">
        Unable to load this booking right now.
      </div>
    );
  }

  const canConfirm = canManageBookings && booking.status === 'pending';
  const canDecline = canManageBookings && booking.status === 'pending';
  const canCancel =
    !canManageBookings && ['pending', 'confirmed', 'active'].includes(booking.status);
  const canRecordReturn =
    canManageBookings && ['confirmed', 'active', 'pending_closure'].includes(booking.status);
  const canCreateAgreement =
    canManageBookings &&
    !agreementLoading &&
    !agreement &&
    ['confirmed', 'active', 'pending_closure', 'closed'].includes(booking.status);
  const canSendAgreement = canManageBookings && agreement?.status === 'draft';
  const canCountersign = canManageBookings && agreement?.status === 'pending_owner_signature';
  const showIdleActionHint = !canConfirm && !canDecline && !canCancel && !canRecordReturn;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-3">
          <Link href="/bookings" className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700">
            <ArrowLeft className="h-4 w-4" />
            Back to bookings
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{booking.booking_number}</h1>
            <BookingStatusBadge status={booking.status} />
            {booking.agreement_status ? (
              <BookingStatusBadge kind="agreement" status={booking.agreement_status} />
            ) : null}
          </div>
          <p className="text-gray-500">
            Submitted {formatBookingDateTime(booking.created_at)} · Updated{' '}
            {formatBookingDateTime(booking.updated_at)}
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.2fr,0.8fr]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Booking summary</CardTitle>
              <CardDescription>
                Stay window, pricing summary, and current workflow state.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="text-lg font-semibold text-gray-900">{booking.property.name}</p>
                    <div className="mt-1 flex items-center gap-2 text-sm text-gray-600">
                      <MapPin className="h-4 w-4 text-gray-400" />
                      <span>{booking.property.location_address ?? 'Location unavailable'}</span>
                    </div>
                  </div>
                  <Link href={`/properties/${booking.property.id}`}>
                    <Button variant="outline">Open property</Button>
                  </Link>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-gray-200 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Stay window
                  </p>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {formatBookingWindow(booking.rental_start_at, booking.rental_end_at)}
                  </p>
                </div>
                <div className="rounded-2xl border border-gray-200 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Actual return
                  </p>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {formatBookingDateTime(booking.actual_return_at)}
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-gray-200 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Total fee
                  </p>
                  <p className="mt-1 text-lg font-semibold text-gray-900">
                    {formatMoney(booking.pricing.total_fee, booking.pricing.currency)}
                  </p>
                </div>
                <div className="rounded-2xl border border-gray-200 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Due now
                  </p>
                  <p className="mt-1 text-lg font-semibold text-gray-900">
                    {formatMoney(booking.pricing.total_due_now, booking.pricing.currency)}
                  </p>
                </div>
                <div className="rounded-2xl border border-gray-200 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Deposit hold
                  </p>
                  <p className="mt-1 text-lg font-semibold text-gray-900">
                    {formatMoney(booking.pricing.deposit_amount, booking.pricing.currency)}
                  </p>
                </div>
                <div className="rounded-2xl border border-gray-200 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Refund amount
                  </p>
                  <p className="mt-1 text-lg font-semibold text-gray-900">
                    {formatMoney(booking.refund_amount, booking.pricing.currency)}
                  </p>
                </div>
              </div>

              {booking.special_requests ? (
                <div className="rounded-2xl border border-gray-200 px-4 py-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Special requests
                  </p>
                  <p className="mt-2 whitespace-pre-wrap text-sm text-gray-600">
                    {booking.special_requests}
                  </p>
                </div>
              ) : null}

              <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-blue-800">
                  <ShieldCheck className="h-4 w-4" />
                  Cancellation policy
                </div>
                <div className="mt-3 grid gap-3 sm:grid-cols-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.16em] text-blue-500">
                      Free cancellation
                    </p>
                    <p className="mt-1 text-sm font-medium text-blue-900">
                      {booking.cancellation_policy.free_cancellation_hours}h
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.16em] text-blue-500">
                      Partial refund window
                    </p>
                    <p className="mt-1 text-sm font-medium text-blue-900">
                      {booking.cancellation_policy.partial_refund_hours}h
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.16em] text-blue-500">
                      Partial refund
                    </p>
                    <p className="mt-1 text-sm font-medium text-blue-900">
                      {booking.cancellation_policy.partial_refund_percent}%
                    </p>
                  </div>
                </div>
              </div>

              {booking.security_deposit ? (
                <div className="rounded-2xl border border-gray-200 px-4 py-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-gray-400">
                    Security deposit record
                  </p>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <div>
                      <p className="text-sm text-gray-500">Status</p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {booking.security_deposit.status}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Gateway reference</p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {booking.security_deposit.gateway_ref ?? '—'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Deduction total</p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {formatMoney(
                          booking.security_deposit.deduction_total,
                          booking.pricing.currency
                        )}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Refund amount</p>
                      <p className="mt-1 text-sm font-medium text-gray-900">
                        {formatMoney(
                          booking.security_deposit.refund_amount,
                          booking.pricing.currency
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <BookingTimeline booking={booking} events={events} />
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">Next actions</CardTitle>
              <CardDescription>
                Role-aware actions for approvals, cancellations, returns, and lease workflow.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {canConfirm ? (
                <Button onClick={() => confirmBooking.mutate({ bookingId: booking.id })} isLoading={confirmBooking.isPending} className="w-full">
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Confirm booking
                </Button>
              ) : null}

              {canDecline ? (
                <div className="space-y-3 rounded-2xl border border-gray-200 p-4">
                  <div>
                    <label htmlFor="decline-reason" className="mb-1 block text-sm font-medium text-gray-700">
                      Decline reason
                    </label>
                    <textarea
                      id="decline-reason"
                      rows={3}
                      value={declineReason}
                      onChange={(event) => setDeclineReason(event.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Explain why this booking cannot be approved."
                    />
                  </div>
                  <Button
                    variant="destructive"
                    onClick={() =>
                      declineBooking.mutate({
                        bookingId: booking.id,
                        data: { reason: declineReason.trim() || 'Declined by property manager' },
                      })
                    }
                    isLoading={declineBooking.isPending}
                    className="w-full"
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Decline booking
                  </Button>
                </div>
              ) : null}

              {canCancel ? (
                <div className="space-y-3 rounded-2xl border border-gray-200 p-4">
                  <div>
                    <label htmlFor="cancel-reason" className="mb-1 block text-sm font-medium text-gray-700">
                      Cancellation reason
                    </label>
                    <textarea
                      id="cancel-reason"
                      rows={3}
                      value={cancelReason}
                      onChange={(event) => setCancelReason(event.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Share why you need to cancel this booking."
                    />
                  </div>
                  <Button
                    variant="destructive"
                    onClick={() =>
                      cancelBooking.mutate({
                        bookingId: booking.id,
                        data: { reason: cancelReason.trim() || 'Cancelled by tenant' },
                      })
                    }
                    isLoading={cancelBooking.isPending}
                    className="w-full"
                  >
                    Cancel booking
                  </Button>
                </div>
              ) : null}

              {canRecordReturn ? (
                <div className="space-y-3 rounded-2xl border border-gray-200 p-4">
                  <Input
                    label="Actual return at"
                    type="datetime-local"
                    value={returnAt}
                    onChange={(event) => setReturnAt(event.target.value)}
                  />
                  <div>
                    <label htmlFor="return-notes" className="mb-1 block text-sm font-medium text-gray-700">
                      Return notes
                    </label>
                    <textarea
                      id="return-notes"
                      rows={3}
                      value={returnNotes}
                      onChange={(event) => setReturnNotes(event.target.value)}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Add notes about inspection, handoff, or close-out."
                    />
                  </div>
                  <Button
                    onClick={() =>
                      returnBooking.mutate({
                        bookingId: booking.id,
                        data: {
                          actual_return_at: returnAt || null,
                          notes: returnNotes.trim(),
                        },
                      })
                    }
                    isLoading={returnBooking.isPending}
                    className="w-full"
                  >
                    <Clock3 className="mr-2 h-4 w-4" />
                    Record return
                  </Button>
                </div>
              ) : showIdleActionHint ? (
                <div className="rounded-2xl border border-dashed border-gray-300 px-4 py-4 text-sm text-gray-500">
                  The next manual actions will appear here when this booking reaches an approval,
                  cancellation, or return milestone.
                </div>
              ) : null}

              {actionError ? (
                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {actionError}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <AgreementSummaryCard
            agreement={agreement}
            isLoading={agreementLoading}
            actions={
              canManageBookings ? (
                <div className="space-y-3">
                  {canCreateAgreement ? (
                    <div className="space-y-3 rounded-2xl border border-gray-200 p-4">
                      <div>
                        <label htmlFor="custom-clauses" className="mb-1 block text-sm font-medium text-gray-700">
                          Custom clauses
                        </label>
                        <textarea
                          id="custom-clauses"
                          rows={4}
                          value={customClauses}
                          onChange={(event) => setCustomClauses(event.target.value)}
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="One clause per line for move-in instructions, utility terms, or other overrides."
                        />
                      </div>
                      <Button
                        onClick={() =>
                          generateAgreement.mutate({
                            bookingId: booking.id,
                            data: { custom_clauses: splitClauses(customClauses) },
                          })
                        }
                        isLoading={generateAgreement.isPending}
                        className="w-full"
                      >
                        <FileSignature className="mr-2 h-4 w-4" />
                        Generate draft agreement
                      </Button>
                    </div>
                  ) : null}

                  {canSendAgreement ? (
                    <Button
                      variant="outline"
                      onClick={() => sendAgreement.mutate({ bookingId: booking.id })}
                      isLoading={sendAgreement.isPending}
                      className="w-full"
                    >
                      Send for tenant signature
                    </Button>
                  ) : null}

                  {canCountersign ? (
                    <Button
                      onClick={() => countersignAgreement.mutate({ bookingId: booking.id })}
                      isLoading={countersignAgreement.isPending}
                      className="w-full"
                    >
                      Countersign agreement
                    </Button>
                  ) : null}
                </div>
              ) : null
            }
          />
        </div>
      </div>
    </div>
  );
}
