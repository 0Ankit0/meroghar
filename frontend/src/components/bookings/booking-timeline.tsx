import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  formatBookingDateTime,
  formatEventType,
} from '@/lib/bookings';
import type { BookingEvent, BookingRecord } from '@/types';

interface TimelineItem {
  id: string;
  title: string;
  description: string;
  occurred_at?: string;
  tone: string;
}

function timelineTone(eventType: string): string {
  if (/confirm|signed|completed|return|closed/i.test(eventType)) {
    return 'bg-emerald-500';
  }

  if (/decline|cancel|terminate|failed/i.test(eventType)) {
    return 'bg-red-500';
  }

  if (/pending|signature/i.test(eventType)) {
    return 'bg-amber-500';
  }

  return 'bg-blue-500';
}

function buildTimeline(booking: BookingRecord, events: BookingEvent[] = []): TimelineItem[] {
  const items: TimelineItem[] = [];

  if (booking.created_at) {
    items.push({
      id: `${booking.id}-created`,
      title: 'Booking submitted',
      description: 'The tenant submitted the initial request.',
      occurred_at: booking.created_at,
      tone: 'bg-blue-500',
    });
  }

  if (booking.confirmed_at) {
    items.push({
      id: `${booking.id}-confirmed`,
      title: 'Booking confirmed',
      description: 'The booking was approved and moved into the active workflow.',
      occurred_at: booking.confirmed_at,
      tone: 'bg-emerald-500',
    });
  }

  if (booking.declined_at) {
    items.push({
      id: `${booking.id}-declined`,
      title: 'Booking declined',
      description: booking.decline_reason || 'The booking request was declined.',
      occurred_at: booking.declined_at,
      tone: 'bg-red-500',
    });
  }

  if (booking.cancelled_at) {
    items.push({
      id: `${booking.id}-cancelled`,
      title: 'Booking cancelled',
      description: booking.cancellation_reason || 'The booking was cancelled.',
      occurred_at: booking.cancelled_at,
      tone: 'bg-red-500',
    });
  }

  if (booking.actual_return_at) {
    items.push({
      id: `${booking.id}-returned`,
      title: 'Return logged',
      description: 'The return workflow has been recorded for this booking.',
      occurred_at: booking.actual_return_at,
      tone: 'bg-emerald-500',
    });
  }

  items.push(
    ...events.map((event) => ({
      id: event.id,
      title: formatEventType(event.event_type),
      description: event.message,
      occurred_at: event.created_at,
      tone: timelineTone(event.event_type),
    }))
  );

  return items.sort((left, right) => {
    const leftTime = left.occurred_at ? new Date(left.occurred_at).getTime() : 0;
    const rightTime = right.occurred_at ? new Date(right.occurred_at).getTime() : 0;
    return leftTime - rightTime;
  });
}

export function BookingTimeline({
  booking,
  events = [],
}: {
  booking: BookingRecord;
  events?: BookingEvent[];
}) {
  const timeline = buildTimeline(booking, events);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Workflow timeline</CardTitle>
        <CardDescription>
          Approval, cancellation, lease, and return events linked to this booking.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {timeline.length ? (
          <div className="space-y-5">
            {timeline.map((item, index) => (
              <div key={item.id} className="relative pl-8">
                {index < timeline.length - 1 ? (
                  <div className="absolute left-[7px] top-4 h-[calc(100%+1.25rem)] w-px bg-gray-200" />
                ) : null}
                <div className={`absolute left-0 top-1.5 h-4 w-4 rounded-full ${item.tone}`} />
                <div className="rounded-2xl border border-gray-200 px-4 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                    <span className="text-xs font-medium text-gray-500">
                      {formatBookingDateTime(item.occurred_at)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-gray-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-gray-300 px-6 py-10 text-center text-sm text-gray-500">
            Timeline events will appear here as the workflow progresses.
          </div>
        )}
      </CardContent>
    </Card>
  );
}
