import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/error/error_handler.dart';
import '../../../applications/presentation/providers/booking_provider.dart';
import '../../data/models/lease_agreement.dart';
import '../agreement_status.dart';
import '../providers/agreement_provider.dart';

class LeaseAgreementPage extends ConsumerWidget {
  final String bookingId;

  const LeaseAgreementPage({
    super.key,
    required this.bookingId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final agreementAsync = ref.watch(bookingAgreementProvider(bookingId));
    final bookingAsync = ref.watch(bookingDetailProvider(bookingId));
    final canSignAgreement = ref.watch(canSignAgreementProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Lease agreement')),
      body: agreementAsync.when(
        loading: () => const Center(child: CircularProgressIndicator.adaptive()),
        error: (error, _) => _LeaseErrorState(
          message: ErrorHandler.handle(error).message,
          onRetry: () => ref.invalidate(bookingAgreementProvider(bookingId)),
        ),
        data: (agreement) {
          if (agreement == null) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'The lease draft is not ready yet. Check back after the application is approved.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      bookingAsync.when(
                        loading: () => const SizedBox.shrink(),
                        error: (_, __) => const SizedBox.shrink(),
                        data: (booking) => Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              booking.property.name,
                              style: Theme.of(context)
                                  .textTheme
                                  .titleLarge
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 4),
                            Text(booking.displayReference),
                            const SizedBox(height: 12),
                          ],
                        ),
                      ),
                      _AgreementStatusChip(
                        agreement: agreement,
                        color: agreement.status
                            .agreementStatusColor(Theme.of(context).colorScheme),
                      ),
                      const SizedBox(height: 12),
                      if (agreement.templateName != null &&
                          agreement.templateName!.trim().isNotEmpty)
                        Text('Template: ${agreement.templateName!}'),
                      if (agreement.summary != null &&
                          agreement.summary!.trim().isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Text(agreement.summary!),
                      ],
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Signature workflow',
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 12),
                      _LeaseInfoRow(
                        label: 'Sent',
                        value: _formatDateTime(agreement.sentAt),
                      ),
                      _LeaseInfoRow(
                        label: 'Tenant signed',
                        value: _formatDateTime(agreement.customerSignedAt),
                      ),
                      _LeaseInfoRow(
                        label: 'Landlord signed',
                        value: _formatDateTime(agreement.ownerSignedAt),
                      ),
                      _LeaseInfoRow(
                        label: 'Request ID',
                        value: agreement.eSignRequestId ?? 'Pending',
                      ),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 12,
                        runSpacing: 12,
                        children: [
                          if (canSignAgreement &&
                              agreement.customerSignUrl != null &&
                              agreement.customerSignUrl!.trim().isNotEmpty &&
                              agreement.needsCustomerSignature)
                            FilledButton.icon(
                              onPressed: () => _openExternalUrl(
                                context,
                                agreement.customerSignUrl!,
                              ),
                              icon: const Icon(Icons.edit_note_outlined),
                              label: const Text('Open signature link'),
                            ),
                          if (agreement.primaryDocumentUrl != null &&
                              agreement.primaryDocumentUrl!.trim().isNotEmpty)
                            OutlinedButton.icon(
                              onPressed: () => _openExternalUrl(
                                context,
                                agreement.primaryDocumentUrl!,
                              ),
                              icon: const Icon(Icons.open_in_new_outlined),
                              label: const Text('Open document'),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Lease preview',
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 12),
                      SelectableText(
                        agreement.renderedContent.trim().isNotEmpty
                            ? agreement.renderedContent
                            : 'The rendered agreement preview is not available yet.',
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _openExternalUrl(BuildContext context, String rawUrl) async {
    final uri = Uri.tryParse(rawUrl);
    if (uri == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid document URL.')),
      );
      return;
    }

    try {
      final launched = await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
      if (!launched && context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Could not open the document link.')),
        );
      }
    } catch (error) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(ErrorHandler.handle(error).message)),
      );
    }
  }
}

class _AgreementStatusChip extends StatelessWidget {
  final LeaseAgreement agreement;
  final Color color;

  const _AgreementStatusChip({
    required this.agreement,
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
          Icon(agreement.status.agreementStatusIcon, color: color, size: 16),
          const SizedBox(width: 6),
          Text(
            agreement.status.agreementStatusLabel,
            style: TextStyle(color: color, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }
}

class _LeaseInfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _LeaseInfoRow({
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

class _LeaseErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _LeaseErrorState({
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

String _formatDateTime(DateTime? value) {
  if (value == null) return 'Pending';
  return DateFormat('MMM d, y • h:mm a').format(value.toLocal());
}
