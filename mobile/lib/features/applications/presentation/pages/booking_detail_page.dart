import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/error/error_handler.dart';
import '../../../lease/presentation/agreement_status.dart';
import '../../../lease/presentation/providers/agreement_provider.dart';
import '../../data/models/booking.dart';
import '../application_status.dart';
import '../providers/booking_provider.dart';

class BookingDetailPage extends ConsumerStatefulWidget {
  final String bookingId;

  const BookingDetailPage({
    super.key,
    required this.bookingId,
  });

  @override
  ConsumerState<BookingDetailPage> createState() => _BookingDetailPageState();
}

class _BookingDetailPageState extends ConsumerState<BookingDetailPage> {
  final _cancelReasonController = TextEditingController();
  bool _cancelling = false;

  @override
  void dispose() {
    _cancelReasonController.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    ref.invalidate(bookingDetailProvider(widget.bookingId));
    ref.invalidate(bookingEventsProvider(widget.bookingId));
    ref.invalidate(bookingAgreementProvider(widget.bookingId));
    try {
      await ref.read(bookingDetailProvider(widget.bookingId).future);
    } catch (_) {}
  }

  Future<void> _cancelBooking() async {
    setState(() => _cancelling = true);
    try {
      await ref.read(bookingRepositoryProvider).cancelBooking(
            widget.bookingId,
            reason: _cancelReasonController.text.trim(),
          );
      ref.invalidate(bookingsProvider);
      await _refresh();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Application cancelled.')),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(ErrorHandler.handle(error).message),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _cancelling = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final bookingAsync = ref.watch(bookingDetailProvider(widget.bookingId));
    final eventsAsync = ref.watch(bookingEventsProvider(widget.bookingId));
    final agreementAsync = ref.watch(bookingAgreementProvider(widget.bookingId));
    final canSubmitApplications = ref.watch(canSubmitApplicationsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Application details')),
      body: bookingAsync.when(
        loading: () => const Center(child: CircularProgressIndicator.adaptive()),
        error: (error, _) => _PageErrorState(
          message: ErrorHandler.handle(error).message,
          onRetry: () => ref.invalidate(bookingDetailProvider(widget.bookingId)),
        ),
        data: (booking) {
          final normalizedStatus = normalizeBookingStatus(booking.status);
          final canCancel = canSubmitApplications &&
              const ['PENDING', 'CONFIRMED', 'ACTIVE']
                  .contains(normalizedStatus);

          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              children: [
                _SummaryCard(booking: booking),
                const SizedBox(height: 16),
                agreementAsync.when(
                  loading: () => const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(
                        child: CircularProgressIndicator.adaptive(),
                      ),
                    ),
                  ),
                  error: (error, _) => _InlineErrorCard(
                    title: 'Lease agreement',
                    message: ErrorHandler.handle(error).message,
                    onRetry: () =>
                        ref.invalidate(bookingAgreementProvider(widget.bookingId)),
                  ),
                  data: (agreement) => Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Lease agreement',
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 12),
                          if (agreement == null)
                            const Text(
                              'The lease draft has not been generated yet. It will appear here once the booking is approved.',
                            )
                          else ...[
                            _StatusChip(
                              icon: agreement.status.agreementStatusIcon,
                              label: agreement.status.agreementStatusLabel,
                              color: agreement.status
                                  .agreementStatusColor(Theme.of(context).colorScheme),
                            ),
                            const SizedBox(height: 12),
                            if (agreement.summary != null &&
                                agreement.summary!.trim().isNotEmpty)
                              Text(agreement.summary!),
                            if (agreement.templateName != null &&
                                agreement.templateName!.trim().isNotEmpty) ...[
                              const SizedBox(height: 8),
                              Text('Template: ${agreement.templateName!}'),
                            ],
                            const SizedBox(height: 12),
                            FilledButton.icon(
                              onPressed: () => context.push(
                                AppConstants.applicationLeaseRoute(
                                  widget.bookingId,
                                ),
                              ),
                              icon: const Icon(Icons.description_outlined),
                              label: const Text('Open lease'),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                if (canCancel)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Cancel application',
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 12),
                          TextFormField(
                            controller: _cancelReasonController,
                            minLines: 2,
                            maxLines: 3,
                            decoration: const InputDecoration(
                              labelText: 'Reason (optional)',
                              border: OutlineInputBorder(),
                            ),
                          ),
                          const SizedBox(height: 12),
                          FilledButton.tonalIcon(
                            onPressed: _cancelling ? null : _cancelBooking,
                            icon: _cancelling
                                ? const SizedBox(
                                    height: 18,
                                    width: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : const Icon(Icons.cancel_outlined),
                            label: const Text('Cancel application'),
                          ),
                        ],
                      ),
                    ),
                  ),
                if (canCancel) const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Timeline',
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 12),
                        eventsAsync.when(
                          loading: () => const Padding(
                            padding: EdgeInsets.symmetric(vertical: 8),
                            child: Center(
                              child: CircularProgressIndicator.adaptive(),
                            ),
                          ),
                          error: (error, _) => _InlineErrorCard(
                            title: '',
                            message: ErrorHandler.handle(error).message,
                            onRetry: () => ref
                                .invalidate(bookingEventsProvider(widget.bookingId)),
                            showTitle: false,
                          ),
                          data: (events) {
                            if (events.isEmpty) {
                              return const Text(
                                'Workflow updates will appear here as this application moves through approval and lease signing.',
                              );
                            }
                            return Column(
                              children: [
                                for (final event in events)
                                  _TimelineTile(event: event),
                              ],
                            );
                          },
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final BookingRecord booking;

  const _SummaryCard({required this.booking});

  @override
  Widget build(BuildContext context) {
    final formatter = DateFormat('MMM d, y');
    final color = booking.status.bookingStatusColor(Theme.of(context).colorScheme);
    final stayLabel = booking.rentalStartAt != null && booking.rentalEndAt != null
        ? '${formatter.format(booking.rentalStartAt!.toLocal())} – ${formatter.format(booking.rentalEndAt!.toLocal())}'
        : 'Stay window pending';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        booking.displayReference,
                        style: Theme.of(context)
                            .textTheme
                            .headlineSmall
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(booking.property.name),
                    ],
                  ),
                ),
                _StatusChip(
                  icon: booking.status.bookingStatusIcon,
                  label: booking.status.bookingStatusLabel,
                  color: color,
                ),
              ],
            ),
            const SizedBox(height: 16),
            _InfoRow(label: 'Stay window', value: stayLabel),
            _InfoRow(
              label: 'Location',
              value: booking.property.locationAddress.isNotEmpty
                  ? booking.property.locationAddress
                  : 'Location unavailable',
            ),
            _InfoRow(
              label: 'Quoted total',
              value: _formatCurrency(
                booking.pricing.totalFee,
                booking.pricing.currency,
              ),
            ),
            _InfoRow(
              label: 'Due now',
              value: _formatCurrency(
                booking.pricing.totalDueNow,
                booking.pricing.currency,
              ),
            ),
            if (booking.specialRequests != null &&
                booking.specialRequests!.trim().isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'Special requests',
                style: Theme.of(context)
                    .textTheme
                    .titleSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              Text(booking.specialRequests!),
            ],
            if (booking.primaryReason != null) ...[
              const SizedBox(height: 12),
              Text(
                'Update',
                style: Theme.of(context)
                    .textTheme
                    .titleSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              Text(booking.primaryReason!),
            ],
          ],
        ),
      ),
    );
  }
}

String _formatCurrency(double amount, String currency) {
  final rounded =
      amount % 1 == 0 ? amount.toStringAsFixed(0) : amount.toStringAsFixed(2);
  return '$currency $rounded';
}

class _TimelineTile extends StatelessWidget {
  final BookingEvent event;

  const _TimelineTile({required this.event});

  @override
  Widget build(BuildContext context) {
    final formatter = DateFormat('MMM d, y • h:mm a');

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 4),
            height: 10,
            width: 10,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  event.title,
                  style: Theme.of(context)
                      .textTheme
                      .titleSmall
                      ?.copyWith(fontWeight: FontWeight.bold),
                ),
                if (event.description != null &&
                    event.description!.trim().isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(event.description!),
                ],
                const SizedBox(height: 4),
                Text(
                  event.createdAt != null
                      ? formatter.format(event.createdAt!.toLocal())
                      : 'Time unavailable',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              value,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;

  const _StatusChip({
    required this.icon,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _InlineErrorCard extends StatelessWidget {
  final String title;
  final String message;
  final VoidCallback onRetry;
  final bool showTitle;

  const _InlineErrorCard({
    required this.title,
    required this.message,
    required this.onRetry,
    this.showTitle = true,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (showTitle && title.isNotEmpty) ...[
          Text(
            title,
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
        ],
        Text(
          message,
          style: TextStyle(color: Theme.of(context).colorScheme.error),
        ),
        const SizedBox(height: 12),
        TextButton(onPressed: onRetry, child: const Text('Retry')),
      ],
    );
  }
}

class _PageErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _PageErrorState({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 12),
            FilledButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}
