import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/error/error_handler.dart';
import '../../data/models/booking.dart';
import '../application_status.dart';
import '../providers/booking_provider.dart';

class ApplicationsPage extends ConsumerWidget {
  const ApplicationsPage({super.key});

  Future<void> _refresh(WidgetRef ref) async {
    ref.invalidate(bookingsProvider);
    try {
      await ref.read(bookingsProvider.future);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final canViewApplications = ref.watch(canViewApplicationsProvider);
    final bookingsAsync = ref.watch(bookingsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My applications')),
      body: !canViewApplications
          ? const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'Application and lease workflows on mobile are reserved for tenant accounts.',
                  textAlign: TextAlign.center,
                ),
              ),
            )
          : RefreshIndicator(
              onRefresh: () => _refresh(ref),
              child: bookingsAsync.when(
                loading: () => ListView(
                  padding: const EdgeInsets.all(24),
                  children: const [
                    SizedBox(height: 200),
                    Center(child: CircularProgressIndicator.adaptive()),
                  ],
                ),
                error: (error, _) => ListView(
                  padding: const EdgeInsets.all(24),
                  children: [
                    _ErrorState(
                      message: ErrorHandler.handle(error).message,
                      onRetry: () => ref.invalidate(bookingsProvider),
                    ),
                  ],
                ),
                data: (bookings) {
                  if (bookings.isEmpty) {
                    return ListView(
                      padding: const EdgeInsets.all(24),
                      children: [
                        const SizedBox(height: 60),
                        Icon(
                          Icons.assignment_outlined,
                          size: 56,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          'No applications yet',
                          textAlign: TextAlign.center,
                          style: Theme.of(context)
                              .textTheme
                              .titleLarge
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Browse listings, request a stay, and your approval and lease updates will appear here.',
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 20),
                        Center(
                          child: FilledButton.icon(
                            onPressed: () =>
                                context.go(AppConstants.listingsRoute),
                            icon: const Icon(Icons.travel_explore_outlined),
                            label: const Text('Browse listings'),
                          ),
                        ),
                      ],
                    );
                  }

                  final pendingCount = bookings
                      .where((booking) =>
                          normalizeBookingStatus(booking.status) == 'PENDING')
                      .length;
                  final activeCount = bookings
                      .where((booking) => const [
                            'CONFIRMED',
                            'ACTIVE',
                            'PENDING_CLOSURE',
                          ].contains(normalizeBookingStatus(booking.status)))
                      .length;

                  return ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    children: [
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            children: [
                              Expanded(
                                child: _MetricTile(
                                  label: 'Applications',
                                  value: bookings.length.toString(),
                                ),
                              ),
                              Expanded(
                                child: _MetricTile(
                                  label: 'Pending',
                                  value: pendingCount.toString(),
                                ),
                              ),
                              Expanded(
                                child: _MetricTile(
                                  label: 'Active',
                                  value: activeCount.toString(),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      for (final booking in bookings) ...[
                        _BookingCard(
                          booking: booking,
                          onTap: () => context.push(
                            AppConstants.applicationDetailRoute(booking.id),
                          ),
                        ),
                        const SizedBox(height: 12),
                      ],
                    ],
                  );
                },
              ),
            ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  final String label;
  final String value;

  const _MetricTile({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: Theme.of(context)
              .textTheme
              .headlineSmall
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}

class _BookingCard extends StatelessWidget {
  final BookingRecord booking;
  final VoidCallback onTap;

  const _BookingCard({
    required this.booking,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final color = booking.status.bookingStatusColor(Theme.of(context).colorScheme);
    final formatter = DateFormat('MMM d, y');
    final stayLabel = booking.rentalStartAt != null && booking.rentalEndAt != null
        ? '${formatter.format(booking.rentalStartAt!.toLocal())} – ${formatter.format(booking.rentalEndAt!.toLocal())}'
        : 'Stay window pending';

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  CircleAvatar(
                    backgroundColor: color.withValues(alpha: 0.12),
                    foregroundColor: color,
                    child: Icon(booking.status.bookingStatusIcon),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          booking.displayReference,
                          style: Theme.of(context)
                              .textTheme
                              .titleMedium
                              ?.copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          booking.property.name,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
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
              const SizedBox(height: 12),
              Text(
                stayLabel,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      booking.property.locationAddress,
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                  Text(
                    _formatCurrency(
                      booking.pricing.totalDueNow,
                      booking.pricing.currency,
                    ),
                    style: Theme.of(context)
                        .textTheme
                        .titleSmall
                        ?.copyWith(fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              if (booking.hasAgreement) ...[
                const SizedBox(height: 10),
                Text(
                  'Lease: ${booking.agreementStatus ?? 'In progress'}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ],
          ),
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

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              message,
              textAlign: TextAlign.center,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: onRetry,
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}
