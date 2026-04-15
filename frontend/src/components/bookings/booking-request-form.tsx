'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { LogIn, Send, Wallet } from 'lucide-react';
import { Button } from '@/components/ui';
import { canCreateBooking, formatBookingWindow, hasBookingManagementAccess } from '@/lib/bookings';
import { formatMoney } from '@/lib/properties';
import { usePaymentProviders } from '@/hooks/use-finances';
import { useCreateBooking } from '@/hooks/use-bookings';
import { useAuthStore } from '@/store/auth-store';
import type { PricingQuote } from '@/types';

function humanizeProvider(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

interface BookingRequestFormProps {
  propertyId: string;
  propertyName: string;
  startAt?: string;
  endAt?: string;
  quote?: PricingQuote | null;
}

export function BookingRequestForm({
  propertyId,
  propertyName,
  startAt,
  endAt,
  quote,
}: BookingRequestFormProps) {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const { data: paymentProviders } = usePaymentProviders();
  const createBooking = useCreateBooking();
  const [paymentMethodId, setPaymentMethodId] = useState('');
  const [specialRequests, setSpecialRequests] = useState('');
  const [localError, setLocalError] = useState('');

  const providerOptions = useMemo(() => {
    const providers = (paymentProviders ?? []).map(String);
    return providers.length ? providers : ['manual_review'];
  }, [paymentProviders]);

  useEffect(() => {
    if (!paymentMethodId || !providerOptions.includes(paymentMethodId)) {
      setPaymentMethodId(providerOptions[0] ?? '');
    }
  }, [paymentMethodId, providerOptions]);

  const canManageBookings = hasBookingManagementAccess(user?.roles, user?.is_superuser);
  const canRequest = canCreateBooking(user?.roles, user?.is_superuser);
  const hasSelectedWindow = Boolean(startAt && endAt);
  const loginHref = `/login?next=${encodeURIComponent(`/properties/${propertyId}`)}`;
  const requestLabel = quote?.total_due
    ? `Submit request for ${formatMoney(quote.total_due, quote.currency)}`
    : 'Submit booking request';

  const handleSubmit = () => {
    if (!hasSelectedWindow || !startAt || !endAt) {
      setLocalError('Pick a move-in and move-out window before sending a booking request.');
      return;
    }

    if (!paymentMethodId.trim()) {
      setLocalError('Choose a payment method before continuing.');
      return;
    }

    setLocalError('');
    createBooking.mutate(
      {
        property_id: propertyId,
        rental_start_at: startAt,
        rental_end_at: endAt,
        special_requests: specialRequests.trim(),
        payment_method_id: paymentMethodId,
        quoted_total_fee: quote?.total_due ?? null,
        quoted_deposit_amount: quote?.deposit_amount ?? null,
        quoted_currency: quote?.currency ?? null,
      },
      {
        onSuccess: (booking) => {
          router.push(`/bookings/${booking.id}`);
        },
      }
    );
  };

  if (!isAuthenticated) {
    return (
      <div className="space-y-3 rounded-2xl border border-dashed border-gray-300 px-4 py-5 text-sm text-gray-600">
        <p>Sign in as a tenant to request this stay and track the approval workflow.</p>
        <Link href={loginHref} className="inline-flex">
          <Button variant="outline">
            <LogIn className="mr-2 h-4 w-4" />
            Sign in to continue
          </Button>
        </Link>
      </div>
    );
  }

  if (!canRequest) {
    return (
      <div className="space-y-3 rounded-2xl border border-dashed border-gray-300 px-4 py-5 text-sm text-gray-600">
        <p>
          Booking submission is limited to tenant accounts. Use the dashboard to manage approvals
          and agreements for existing requests.
        </p>
        {canManageBookings ? (
          <Link href="/bookings" className="inline-flex">
            <Button variant="outline">Open bookings dashboard</Button>
          </Link>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
        <p className="text-sm font-semibold text-gray-900">{propertyName}</p>
        <p className="mt-1 text-sm text-gray-600">
          {hasSelectedWindow
            ? formatBookingWindow(startAt, endAt)
            : 'Select a quote window above to request this stay.'}
        </p>
        {quote ? (
          <div className="mt-3 grid gap-2 text-sm text-gray-600 sm:grid-cols-2">
            <div className="rounded-xl bg-white px-3 py-2">
              Due now: <span className="font-semibold text-gray-900">{formatMoney(quote.total_due, quote.currency)}</span>
            </div>
            <div className="rounded-xl bg-white px-3 py-2">
              Deposit: <span className="font-semibold text-gray-900">{formatMoney(quote.deposit_amount ?? 0, quote.currency)}</span>
            </div>
          </div>
        ) : null}
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">Payment method</label>
        <div className="relative">
          <Wallet className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <select
            value={paymentMethodId}
            onChange={(event) => setPaymentMethodId(event.target.value)}
            className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {providerOptions.map((provider) => (
              <option key={provider} value={provider}>
                {humanizeProvider(provider)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="special-requests" className="mb-1 block text-sm font-medium text-gray-700">
          Special requests
        </label>
        <textarea
          id="special-requests"
          rows={4}
          value={specialRequests}
          onChange={(event) => setSpecialRequests(event.target.value)}
          placeholder="Add move-in notes, furnishing requests, or questions for the property team."
          className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {localError ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {localError}
        </div>
      ) : null}

      {createBooking.error ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {createBooking.error instanceof Error
            ? createBooking.error.message
            : 'Unable to create the booking right now.'}
        </div>
      ) : null}

      <Button onClick={handleSubmit} isLoading={createBooking.isPending} className="w-full">
        <Send className="mr-2 h-4 w-4" />
        {requestLabel}
      </Button>
    </div>
  );
}
