import {
  agreementStatusTone,
  bookingStatusTone,
  formatAgreementStatus,
  formatBookingStatus,
} from '@/lib/bookings';

interface BookingStatusBadgeProps {
  status?: string | null;
  kind?: 'booking' | 'agreement';
  className?: string;
}

export function BookingStatusBadge({
  status,
  kind = 'booking',
  className = '',
}: BookingStatusBadgeProps) {
  const tone = kind === 'agreement' ? agreementStatusTone(status) : bookingStatusTone(status);
  const label = kind === 'agreement' ? formatAgreementStatus(status) : formatBookingStatus(status);

  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${tone} ${className}`.trim()}
    >
      {label}
    </span>
  );
}
