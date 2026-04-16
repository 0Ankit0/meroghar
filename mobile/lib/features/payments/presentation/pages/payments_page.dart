import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/analytics/analytics_events.dart';
import '../../../../core/analytics/analytics_provider.dart';
import '../../../../core/error/error_handler.dart';
import '../../../applications/data/models/booking.dart';
import '../../../applications/presentation/providers/booking_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/models/billing.dart';
import '../../data/models/payment.dart';
import '../../payment_access.dart';
import '../providers/payment_provider.dart';
import 'payment_utils.dart';
import 'payment_webview_page.dart';

final DateFormat _billingDateFormat = DateFormat('MMM d, y');

String _formatCurrency(double amount, String currency) {
  final rounded =
      amount % 1 == 0 ? amount.toStringAsFixed(0) : amount.toStringAsFixed(2);
  return '$currency $rounded';
}

String _formatDate(DateTime? value) {
  if (value == null) return '—';
  return _billingDateFormat.format(value.toLocal());
}

String _formatPeriod(DateTime? start, DateTime? end) {
  if (start == null && end == null) return 'Period pending';
  if (start != null && end != null) {
    return '${DateFormat('MMM d').format(start.toLocal())} – ${_billingDateFormat.format(end.toLocal())}';
  }
  return _formatDate(start ?? end);
}

Color _invoiceStatusColor(BuildContext context, InvoiceStatus status) {
  switch (status) {
    case InvoiceStatus.paid:
      return Colors.green;
    case InvoiceStatus.partiallyPaid:
      return Colors.orange;
    case InvoiceStatus.overdue:
      return Theme.of(context).colorScheme.error;
    case InvoiceStatus.waived:
      return Colors.blueGrey;
    case InvoiceStatus.draft:
      return Colors.grey;
    case InvoiceStatus.sent:
      return Colors.indigo;
  }
}

Color _billShareStatusColor(
    BuildContext context, UtilityBillSplitStatus status) {
  switch (status) {
    case UtilityBillSplitStatus.paid:
      return Colors.green;
    case UtilityBillSplitStatus.partiallyPaid:
      return Colors.orange;
    case UtilityBillSplitStatus.disputed:
      return Theme.of(context).colorScheme.error;
    case UtilityBillSplitStatus.waived:
      return Colors.blueGrey;
    case UtilityBillSplitStatus.pending:
      return Colors.indigo;
  }
}

Color _paymentStatusColor(BuildContext context, PaymentStatus status) {
  switch (status) {
    case PaymentStatus.completed:
      return Colors.green;
    case PaymentStatus.failed:
      return Theme.of(context).colorScheme.error;
    case PaymentStatus.refunded:
      return Colors.blue;
    case PaymentStatus.cancelled:
      return Colors.grey;
    case PaymentStatus.initiated:
    case PaymentStatus.pending:
      return Colors.orange;
  }
}

double _displayTransactionAmount(PaymentTransaction transaction) {
  switch (transaction.provider) {
    case PaymentProvider.esewa:
      return transaction.amount.toDouble();
    case PaymentProvider.khalti:
    case PaymentProvider.stripe:
    case PaymentProvider.paypal:
      return transaction.amount / 100;
  }
}

class PaymentsPage extends ConsumerStatefulWidget {
  const PaymentsPage({super.key});

  @override
  ConsumerState<PaymentsPage> createState() => _PaymentsPageState();
}

class _PaymentsPageState extends ConsumerState<PaymentsPage> {
  static const _callbackUrlPrefix = 'http://localhost:3000/payment-callback';
  static const _websiteUrl = 'http://localhost:3000';

  Future<void> _awaitSilently(Future<dynamic> future) async {
    try {
      await future;
    } catch (_) {}
  }

  Future<void> _refreshAll() async {
    final invoices =
        ref.read(invoicesProvider).valueOrNull ?? const <InvoiceSummary>[];
    final billShares = ref.read(tenantBillSharesProvider).valueOrNull ??
        const <UtilityBillShare>[];

    final bookingIds = <String>{
      for (final invoice in invoices)
        if (invoice.bookingId != null && invoice.bookingId!.isNotEmpty)
          invoice.bookingId!,
    };

    for (final invoice in invoices) {
      ref.invalidate(invoiceDetailProvider(invoice.id));
      ref.invalidate(invoiceReceiptProvider(invoice.id));
    }
    for (final bookingId in bookingIds) {
      ref.invalidate(rentLedgerProvider(bookingId));
    }
    for (final share in billShares) {
      ref.invalidate(utilityBillHistoryProvider(share.bill.id));
      final invoiceId = share.split.invoiceId;
      if (invoiceId != null && invoiceId.isNotEmpty) {
        ref.invalidate(invoiceReceiptProvider(invoiceId));
      }
    }

    ref.invalidate(invoicesProvider);
    ref.invalidate(tenantBillSharesProvider);
    ref.invalidate(transactionsProvider);
    ref.invalidate(bookingsProvider);

    await Future.wait([
      _awaitSilently(ref.read(invoicesProvider.future)),
      _awaitSilently(ref.read(tenantBillSharesProvider.future)),
      _awaitSilently(ref.read(transactionsProvider.future)),
      _awaitSilently(ref.read(bookingsProvider.future)),
    ]);
  }

  Future<T?> _showBillingSheet<T>(WidgetBuilder builder) {
    return showModalBottomSheet<T>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      builder: (sheetContext) => FractionallySizedBox(
        heightFactor: 0.92,
        child: builder(sheetContext),
      ),
    );
  }

  String _bookingTitle(String? bookingId) {
    if (bookingId == null || bookingId.isEmpty) return 'Rent ledger';
    final bookings =
        ref.read(bookingsProvider).valueOrNull ?? const <BookingRecord>[];
    for (final booking in bookings) {
      if (booking.id == bookingId) {
        return booking.property.name.isNotEmpty
            ? booking.property.name
            : booking.displayReference;
      }
    }
    return 'Booking $bookingId';
  }

  void _showSnack(String message, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: error ? Theme.of(context).colorScheme.error : null,
      ),
    );
  }

  Future<void> _startInvoiceCheckout(InvoiceSummary invoice) async {
    final selection = await _showBillingSheet<_BillingCheckoutSelection>(
      (_) => _BillingCheckoutSheet(
        title: invoice.displayTitle,
        currency: invoice.currency,
        outstandingAmount: invoice.outstandingAmount,
        allowPartial: invoice.canPartialPay,
        description: 'Choose how you want to settle this invoice.',
      ),
    );
    if (selection == null) return;

    try {
      final response = await ref.read(paymentRepositoryProvider).payInvoice(
            invoice.id,
            BillingPaymentRequest(
              provider: selection.provider,
              amount: selection.amount,
              returnUrl: _callbackUrlPrefix,
              websiteUrl: _websiteUrl,
            ),
            partial: selection.amount != null,
          );

      ref.read(analyticsServiceProvider).capture(
        PaymentAnalyticsEvents.paymentInitiated,
        {
          'provider': selection.provider.name,
          'amount': selection.amount ?? invoice.outstandingAmount,
          'target': 'invoice',
          'invoice_id': invoice.id,
        },
      );

      if (!mounted) return;
      final result = await _openPaymentWebView(response);
      if (!mounted) return;

      if (result != null) {
        await _refreshAll();
      } else {
        ref.invalidate(transactionsProvider);
      }
    } catch (error) {
      if (!mounted) return;
      _showSnack(ErrorHandler.handle(error).message, error: true);
    }
  }

  Future<void> _startBillShareCheckout(UtilityBillShare share) async {
    final selection = await _showBillingSheet<_BillingCheckoutSelection>(
      (_) => _BillingCheckoutSheet(
        title: share.bill.displayTitle,
        currency: 'NPR',
        outstandingAmount: share.split.outstandingAmount,
        allowPartial: false,
        description: 'Choose a provider to pay this utility bill share.',
      ),
    );
    if (selection == null) return;

    try {
      final response = await ref.read(paymentRepositoryProvider).payBillShare(
            share.split.id,
            BillingPaymentRequest(
              provider: selection.provider,
              returnUrl: _callbackUrlPrefix,
              websiteUrl: _websiteUrl,
            ),
          );

      ref.read(analyticsServiceProvider).capture(
        PaymentAnalyticsEvents.paymentInitiated,
        {
          'provider': selection.provider.name,
          'amount': share.split.outstandingAmount,
          'target': 'bill_share',
          'bill_share_id': share.split.id,
        },
      );

      if (!mounted) return;
      final result = await _openPaymentWebView(response);
      if (!mounted) return;

      if (result != null) {
        await _refreshAll();
      } else {
        ref.invalidate(transactionsProvider);
      }
    } catch (error) {
      if (!mounted) return;
      _showSnack(ErrorHandler.handle(error).message, error: true);
    }
  }

  Future<void> _openDisputeComposer(UtilityBillShare share) async {
    final controller = TextEditingController();
    String? validationMessage;

    final reason = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Dispute utility share'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Explain what looks incorrect about ${share.bill.displayTitle.toLowerCase()}.',
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: controller,
                    minLines: 3,
                    maxLines: 5,
                    autofocus: true,
                    decoration: InputDecoration(
                      labelText: 'Reason',
                      border: const OutlineInputBorder(),
                      errorText: validationMessage,
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () {
                    final trimmed = controller.text.trim();
                    if (trimmed.isEmpty) {
                      setDialogState(() {
                        validationMessage = 'Please share a dispute reason.';
                      });
                      return;
                    }
                    Navigator.of(dialogContext).pop(trimmed);
                  },
                  child: const Text('Submit dispute'),
                ),
              ],
            );
          },
        );
      },
    );

    controller.dispose();
    if (reason == null || reason.trim().isEmpty) return;

    try {
      await ref.read(paymentRepositoryProvider).disputeBillShare(
            share.split.id,
            BillShareDisputeRequest(reason: reason),
          );
      if (!mounted) return;
      await _refreshAll();
      if (!mounted) return;
      _showSnack('Dispute submitted for review.');
    } catch (error) {
      if (!mounted) return;
      _showSnack(ErrorHandler.handle(error).message, error: true);
    }
  }

  Future<void> _openAdditionalChargeDisputeComposer(
    AdditionalChargeSummary charge,
  ) async {
    final controller = TextEditingController();
    String? validationMessage;

    final reason = await showDialog<String>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Dispute additional charge'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Explain what should be reviewed about ${charge.description.toLowerCase()}.',
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: controller,
                    minLines: 3,
                    maxLines: 5,
                    autofocus: true,
                    decoration: InputDecoration(
                      labelText: 'Reason',
                      border: const OutlineInputBorder(),
                      errorText: validationMessage,
                    ),
                  ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(dialogContext).pop(),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: () {
                    final trimmed = controller.text.trim();
                    if (trimmed.isEmpty) {
                      setDialogState(() {
                        validationMessage = 'Please share a dispute reason.';
                      });
                      return;
                    }
                    Navigator.of(dialogContext).pop(trimmed);
                  },
                  child: const Text('Submit dispute'),
                ),
              ],
            );
          },
        );
      },
    );

    controller.dispose();
    if (reason == null || reason.trim().isEmpty) return;

    try {
      await ref.read(paymentRepositoryProvider).disputeAdditionalCharge(
            charge.id,
            reason,
          );
      if (!mounted) return;
      await _refreshAll();
      if (!mounted) return;
      _showSnack('Charge dispute submitted for review.');
    } catch (error) {
      if (!mounted) return;
      _showSnack(ErrorHandler.handle(error).message, error: true);
    }
  }

  Future<void> _showInvoiceDetails(InvoiceSummary invoice) async {
    await _showBillingSheet<void>(
      (sheetContext) => Consumer(
        builder: (context, ref, _) {
          final detailAsync = ref.watch(invoiceDetailProvider(invoice.id));
          return detailAsync.when(
            loading: () => const _SheetLoading(title: 'Invoice details'),
            error: (error, _) => _SheetError(
              title: 'Invoice details',
              message: ErrorHandler.handle(error).message,
              onRetry: () => ref.invalidate(invoiceDetailProvider(invoice.id)),
            ),
            data: (detail) => _InvoiceDetailSheet(
              invoice: detail,
              onPay: detail.canPay
                  ? () {
                      Navigator.of(sheetContext).pop();
                      _startInvoiceCheckout(detail);
                    }
                  : null,
              onShowReceipt: detail.canShowReceipt
                  ? () {
                      Navigator.of(sheetContext).pop();
                      _showInvoiceReceipt(detail.id,
                          title: detail.displayTitle);
                    }
                  : null,
              onShowLedger: detail.bookingId == null
                  ? null
                  : () {
                      Navigator.of(sheetContext).pop();
                      _showRentLedger(
                        detail.bookingId!,
                        title: _bookingTitle(detail.bookingId),
                      );
                    },
            ),
          );
        },
      ),
    );
  }

  Future<void> _showInvoiceReceipt(
    String invoiceId, {
    required String title,
  }) async {
    await _showBillingSheet<void>(
      (_) => Consumer(
        builder: (context, ref, _) {
          final receiptAsync = ref.watch(invoiceReceiptProvider(invoiceId));
          return receiptAsync.when(
            loading: () => _SheetLoading(title: '$title receipt'),
            error: (error, _) => _SheetError(
              title: '$title receipt',
              message: ErrorHandler.handle(error).message,
              onRetry: () => ref.invalidate(invoiceReceiptProvider(invoiceId)),
            ),
            data: (receipt) => _ReceiptSheet(
              title: '$title receipt',
              receipt: receipt,
            ),
          );
        },
      ),
    );
  }

  Future<void> _showRentLedger(
    String bookingId, {
    required String title,
  }) async {
    await _showBillingSheet<void>(
      (sheetContext) => Consumer(
        builder: (context, ref, _) {
          final ledgerAsync = ref.watch(rentLedgerProvider(bookingId));
          return ledgerAsync.when(
            loading: () => _SheetLoading(title: '$title ledger'),
            error: (error, _) => _SheetError(
              title: '$title ledger',
              message: ErrorHandler.handle(error).message,
              onRetry: () => ref.invalidate(rentLedgerProvider(bookingId)),
            ),
            data: (ledger) => _RentLedgerSheet(
              title: '$title ledger',
              ledger: ledger,
              onDisputeCharge: (charge) {
                Navigator.of(sheetContext).pop();
                _openAdditionalChargeDisputeComposer(charge);
              },
            ),
          );
        },
      ),
    );
  }

  Future<void> _showUtilityBillHistory(UtilityBillShare share) async {
    await _showBillingSheet<void>(
      (sheetContext) => Consumer(
        builder: (context, ref, _) {
          final historyAsync =
              ref.watch(utilityBillHistoryProvider(share.bill.id));
          return historyAsync.when(
            loading: () => _SheetLoading(title: share.bill.displayTitle),
            error: (error, _) => _SheetError(
              title: share.bill.displayTitle,
              message: ErrorHandler.handle(error).message,
              onRetry: () =>
                  ref.invalidate(utilityBillHistoryProvider(share.bill.id)),
            ),
            data: (history) => _UtilityBillHistorySheet(
              share: share,
              history: history,
              onPay: share.canPay
                  ? () {
                      Navigator.of(sheetContext).pop();
                      _startBillShareCheckout(share);
                    }
                  : null,
              onDispute: share.canDispute
                  ? () {
                      Navigator.of(sheetContext).pop();
                      _openDisputeComposer(share);
                    }
                  : null,
              onShowReceipt: share.canShowReceipt
                  ? () {
                      Navigator.of(sheetContext).pop();
                      _showInvoiceReceipt(
                        share.split.invoiceId!,
                        title: share.bill.displayTitle,
                      );
                    }
                  : null,
              onOpenAttachment: _openAttachment,
            ),
          );
        },
      ),
    );
  }

  Future<void> _openAttachment(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) {
      _showSnack('Attachment link is unavailable.', error: true);
      return;
    }

    try {
      final launched = await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
      if (!launched && mounted) {
        _showSnack('Could not open the attachment.', error: true);
      }
    } catch (error) {
      if (!mounted) return;
      _showSnack(ErrorHandler.handle(error).message, error: true);
    }
  }

  Future<PaymentResult?> _openPaymentWebView(
    InitiatePaymentResponse response,
  ) async {
    if (kIsWeb) {
      await _handleWebPayment(response);
      return null;
    }

    final rawEsewaFields = response.extra?['form_fields'];
    final esewaFields = rawEsewaFields is Map
        ? rawEsewaFields.map(
            (key, value) => MapEntry(key.toString(), value),
          )
        : null;

    final result = await Navigator.of(context).push<PaymentResult>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => UncontrolledProviderScope(
          container: ProviderScope.containerOf(context),
          child: PaymentWebViewPage(
            provider: response.provider,
            paymentUrl: response.paymentUrl,
            esewaFormAction: response.extra?['form_action'] as String?,
            esewaFormFields: esewaFields,
            callbackUrlPrefix: _callbackUrlPrefix,
          ),
        ),
      ),
    );

    if (!mounted || result == null) return result;

    ref.read(analyticsServiceProvider).capture(
      result.success
          ? PaymentAnalyticsEvents.paymentCompleted
          : PaymentAnalyticsEvents.paymentFailed,
      {'provider': response.provider.name},
    );
    _showSnack(result.message, error: !result.success);
    return result;
  }

  Future<void> _handleWebPayment(InitiatePaymentResponse response) async {
    try {
      if (response.provider == PaymentProvider.esewa) {
        final formAction = response.extra?['form_action'] as String? ??
            'https://rc-epay.esewa.com.np/api/epay/main/v2/form';
        final formFields = response.extra?['form_fields'];
        final payload = formFields is Map
            ? formFields.map((key, value) => MapEntry(key.toString(), value))
            : const <String, dynamic>{};
        await submitEsewaFormWeb(formAction, payload);
      } else {
        final url = response.paymentUrl;
        if (url != null) {
          await launchUrl(
            Uri.parse(url),
            mode: LaunchMode.externalApplication,
          );
        }
      }
      if (!mounted) return;
      _showSnack(
        'Complete the payment in your browser, then refresh billing to see the latest status.',
      );
    } catch (error) {
      if (!mounted) return;
      _showSnack('Could not open payment page: $error', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authNotifierProvider).valueOrNull;
    final roles = authState?.user?.roles ?? const <String>[];
    final canUseTenantBilling = canViewTenantBilling(roles);
    final shouldUseWebsiteForManagement =
        (authState?.user?.isSuperuser ?? false) ||
        shouldUseWebsiteForBillingManagement(roles);

    if (!canUseTenantBilling) {
      return Scaffold(
        appBar: AppBar(title: const Text('Billing')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(
                      Icons.desktop_windows_outlined,
                      size: 40,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Tenant billing stays on mobile',
                      style: Theme.of(context)
                          .textTheme
                          .titleLarge
                          ?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      shouldUseWebsiteForManagement
                          ? 'Use the website for owner and admin billing management, including utility bill setup, split publishing, and dispute resolution.'
                          : 'This account does not currently expose tenant billing workflows on mobile.',
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    }

    final invoicesAsync = ref.watch(invoicesProvider);
    final bookingsAsync = ref.watch(bookingsProvider);
    final billSharesAsync = ref.watch(tenantBillSharesProvider);
    final transactionsAsync = ref.watch(transactionsProvider);

    final allInvoices = invoicesAsync.valueOrNull ?? const <InvoiceSummary>[];
    final rentInvoices = allInvoices
        .where((invoice) => invoice.invoiceType != InvoiceType.utilityBillShare)
        .toList()
      ..sort((a, b) {
        final aDate =
            a.dueDate ?? a.createdAt ?? DateTime.fromMillisecondsSinceEpoch(0);
        final bDate =
            b.dueDate ?? b.createdAt ?? DateTime.fromMillisecondsSinceEpoch(0);
        return aDate.compareTo(bDate);
      });
    final billShares =
        billSharesAsync.valueOrNull ?? const <UtilityBillShare>[];
    final bookings = bookingsAsync.valueOrNull ?? const <BookingRecord>[];
    final bookingsById = {
      for (final booking in bookings)
        if (booking.id.isNotEmpty) booking.id: booking,
    };

    final rentOutstanding = rentInvoices.fold<double>(
      0,
      (total, invoice) => total + invoice.outstandingAmount,
    );
    final utilityOutstanding = billShares.fold<double>(
      0,
      (total, share) => total + share.split.outstandingAmount,
    );

    final ledgerBookingIds = <String>{
      for (final invoice in rentInvoices)
        if (invoice.bookingId != null && invoice.bookingId!.isNotEmpty)
          invoice.bookingId!,
    };
    if (ledgerBookingIds.isEmpty) {
      ledgerBookingIds.addAll(
        bookings
            .where(
              (booking) => const [
                'CONFIRMED',
                'ACTIVE',
                'PENDING_CLOSURE',
                'CLOSED'
              ].contains(booking.status),
            )
            .map((booking) => booking.id)
            .where((id) => id.isNotEmpty),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Billing'),
        actions: [
          IconButton(
            tooltip: 'Refresh billing',
            onPressed: _refreshAll,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refreshAll,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            _BillingOverviewCard(
              rentOutstanding: rentOutstanding,
              utilityOutstanding: utilityOutstanding,
              totalOutstanding: rentOutstanding + utilityOutstanding,
              rentInvoiceCount: rentInvoices.length,
              utilityShareCount: billShares.length,
            ),
            const SizedBox(height: 24),
            const _SectionHeader(
              title: 'Rent invoices',
              subtitle:
                  'Review monthly rent and additional charge invoices, then pay or open receipts when you need them.',
            ),
            const SizedBox(height: 12),
            invoicesAsync.when(
              loading: () => const _SectionLoading(),
              error: (error, _) => _SectionErrorCard(
                message: ErrorHandler.handle(error).message,
                onRetry: () => ref.invalidate(invoicesProvider),
              ),
              data: (_) {
                if (rentInvoices.isEmpty) {
                  return const _SectionEmptyCard(
                    icon: Icons.receipt_long_outlined,
                    title: 'No rent invoices yet',
                    subtitle:
                        'Monthly invoices will appear here once your tenancy billing cycle starts.',
                  );
                }

                return Column(
                  children: rentInvoices
                      .map(
                        (invoice) => _InvoiceCard(
                          invoice: invoice,
                          bookingLabel: invoice.bookingId == null
                              ? null
                              : bookingsById[invoice.bookingId!]?.property.name,
                          onOpenDetails: () => _showInvoiceDetails(invoice),
                          onPay: invoice.canPay
                              ? () => _startInvoiceCheckout(invoice)
                              : null,
                          onShowReceipt: invoice.canShowReceipt
                              ? () => _showInvoiceReceipt(
                                    invoice.id,
                                    title: invoice.displayTitle,
                                  )
                              : null,
                          onShowLedger: invoice.bookingId == null
                              ? null
                              : () => _showRentLedger(
                                    invoice.bookingId!,
                                    title: _bookingTitle(invoice.bookingId),
                                  ),
                        ),
                      )
                      .toList(),
                );
              },
            ),
            const SizedBox(height: 24),
            const _SectionHeader(
              title: 'Rent ledger',
              subtitle:
                  'Open the monthly rent schedule and invoice timeline for each tenancy tied to your mobile account.',
            ),
            const SizedBox(height: 12),
            if (ledgerBookingIds.isEmpty && bookingsAsync.isLoading)
              const _SectionLoading()
            else if (ledgerBookingIds.isEmpty)
              const _SectionEmptyCard(
                icon: Icons.timeline_outlined,
                title: 'No rent ledger available yet',
                subtitle:
                    'Once a booking moves into active billing, the ledger timeline will show the due schedule here.',
              )
            else
              Column(
                children: ledgerBookingIds
                    .map(
                      (bookingId) => Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor:
                                Colors.indigo.withValues(alpha: 0.12),
                            child: const Icon(
                              Icons.timeline_outlined,
                              color: Colors.indigo,
                            ),
                          ),
                          title: Text(
                            _bookingTitle(bookingId),
                            style: const TextStyle(fontWeight: FontWeight.w600),
                          ),
                          subtitle: Text(
                            bookingsById[bookingId]?.displayReference ??
                                'Open the rent timeline and totals for this booking.',
                          ),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => _showRentLedger(
                            bookingId,
                            title: _bookingTitle(bookingId),
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            const SizedBox(height: 24),
            const _SectionHeader(
              title: 'Utility bill shares',
              subtitle:
                  'Track tenant bill splits, inspect the published history, and raise disputes before they are settled.',
            ),
            const SizedBox(height: 12),
            billSharesAsync.when(
              loading: () => const _SectionLoading(),
              error: (error, _) => _SectionErrorCard(
                message: ErrorHandler.handle(error).message,
                onRetry: () => ref.invalidate(tenantBillSharesProvider),
              ),
              data: (shares) {
                if (shares.isEmpty) {
                  return const _SectionEmptyCard(
                    icon: Icons.bolt_outlined,
                    title: 'No utility bill shares',
                    subtitle:
                        'Published utility splits will appear here after the owner or manager finishes setup on the website.',
                  );
                }

                return Column(
                  children: shares
                      .map(
                        (share) => _BillShareCard(
                          share: share,
                          onOpenHistory: () => _showUtilityBillHistory(share),
                          onPay: share.canPay
                              ? () => _startBillShareCheckout(share)
                              : null,
                          onDispute: share.canDispute
                              ? () => _openDisputeComposer(share)
                              : null,
                          onShowReceipt: share.canShowReceipt
                              ? () => _showInvoiceReceipt(
                                    share.split.invoiceId!,
                                    title: share.bill.displayTitle,
                                  )
                              : null,
                        ),
                      )
                      .toList(),
                );
              },
            ),
            const SizedBox(height: 24),
            const _SectionHeader(
              title: 'Transaction history',
              subtitle:
                  'Recent checkout attempts stay here as a supporting audit trail for your tenant billing activity.',
            ),
            const SizedBox(height: 12),
            _TransactionHistorySection(transactionsAsync: transactionsAsync),
          ],
        ),
      ),
    );
  }
}

class _BillingCheckoutSelection {
  final PaymentProvider provider;
  final double? amount;

  const _BillingCheckoutSelection({
    required this.provider,
    this.amount,
  });
}

class _BillingOverviewCard extends StatelessWidget {
  final double rentOutstanding;
  final double utilityOutstanding;
  final double totalOutstanding;
  final int rentInvoiceCount;
  final int utilityShareCount;

  const _BillingOverviewCard({
    required this.rentOutstanding,
    required this.utilityOutstanding,
    required this.totalOutstanding,
    required this.rentInvoiceCount,
    required this.utilityShareCount,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Tenant billing',
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Pay rent invoices, review receipts, and keep up with utility bill shares. Owners and managers still create bills and configure splits on the website.',
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _SummaryMetric(
                    label: 'Rent due',
                    value: _formatCurrency(rentOutstanding, 'NPR'),
                    hint:
                        '$rentInvoiceCount invoice${rentInvoiceCount == 1 ? '' : 's'}',
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _SummaryMetric(
                    label: 'Utility due',
                    value: _formatCurrency(utilityOutstanding, 'NPR'),
                    hint:
                        '$utilityShareCount share${utilityShareCount == 1 ? '' : 's'}',
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _SummaryMetric(
                    label: 'Total due',
                    value: _formatCurrency(totalOutstanding, 'NPR'),
                    hint: totalOutstanding > 0 ? 'Action needed' : 'All clear',
                    emphasize: true,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryMetric extends StatelessWidget {
  final String label;
  final String value;
  final String hint;
  final bool emphasize;

  const _SummaryMetric({
    required this.label,
    required this.value,
    required this.hint,
    this.emphasize = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = emphasize ? Theme.of(context).colorScheme.primary : null;
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: (color ?? Colors.black).withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelMedium),
          const SizedBox(height: 6),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
          ),
          const SizedBox(height: 4),
          Text(hint, style: Theme.of(context).textTheme.bodySmall),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final String subtitle;

  const _SectionHeader({
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _SectionLoading extends StatelessWidget {
  const _SectionLoading();

  @override
  Widget build(BuildContext context) {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Center(child: CircularProgressIndicator.adaptive()),
      ),
    );
  }
}

class _SectionErrorCard extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _SectionErrorCard({
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 12),
            FilledButton.tonalIcon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Try again'),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionEmptyCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const _SectionEmptyCard({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            Icon(icon, size: 40, color: Colors.grey),
            const SizedBox(height: 12),
            Text(
              title,
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final String label;
  final Color color;

  const _StatusBadge({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
    );
  }
}

class _InvoiceCard extends StatelessWidget {
  final InvoiceSummary invoice;
  final String? bookingLabel;
  final VoidCallback onOpenDetails;
  final VoidCallback? onPay;
  final VoidCallback? onShowReceipt;
  final VoidCallback? onShowLedger;

  const _InvoiceCard({
    required this.invoice,
    this.bookingLabel,
    required this.onOpenDetails,
    this.onPay,
    this.onShowReceipt,
    this.onShowLedger,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
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
                        invoice.displayTitle,
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${invoice.invoiceType.displayName} • Due ${_formatDate(invoice.dueDate)}',
                      ),
                      if (bookingLabel != null &&
                          bookingLabel!.trim().isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(
                          bookingLabel!,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ],
                  ),
                ),
                _StatusBadge(
                  label: invoice.status.displayName,
                  color: _invoiceStatusColor(context, invoice.status),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _AmountChip(
                  label: 'Total',
                  value: _formatCurrency(invoice.totalAmount, invoice.currency),
                ),
                _AmountChip(
                  label: 'Paid',
                  value: _formatCurrency(invoice.paidAmount, invoice.currency),
                ),
                _AmountChip(
                  label: 'Outstanding',
                  value: _formatCurrency(
                      invoice.outstandingAmount, invoice.currency),
                  emphasize: invoice.outstandingAmount > 0.01,
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _formatPeriod(invoice.periodStart, invoice.periodEnd),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            if (invoice.canPartialPay) ...[
              const SizedBox(height: 6),
              Text(
                'Custom partial amounts are available during checkout.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: onOpenDetails,
                  icon: const Icon(Icons.open_in_full_outlined),
                  label: const Text('Details'),
                ),
                if (onShowLedger != null)
                  OutlinedButton.icon(
                    onPressed: onShowLedger,
                    icon: const Icon(Icons.timeline_outlined),
                    label: const Text('Ledger'),
                  ),
                if (onShowReceipt != null)
                  OutlinedButton.icon(
                    onPressed: onShowReceipt,
                    icon: const Icon(Icons.receipt_long_outlined),
                    label: const Text('Receipt'),
                  ),
                if (onPay != null)
                  FilledButton.icon(
                    onPressed: onPay,
                    icon: const Icon(Icons.payment_outlined),
                    label: const Text('Pay'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _AmountChip extends StatelessWidget {
  final String label;
  final String value;
  final bool emphasize;

  const _AmountChip({
    required this.label,
    required this.value,
    this.emphasize = false,
  });

  @override
  Widget build(BuildContext context) {
    final color = emphasize ? Theme.of(context).colorScheme.primary : null;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: (color ?? Colors.black).withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.labelSmall),
          const SizedBox(height: 2),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
          ),
        ],
      ),
    );
  }
}

class _BillShareCard extends StatelessWidget {
  final UtilityBillShare share;
  final VoidCallback onOpenHistory;
  final VoidCallback? onPay;
  final VoidCallback? onDispute;
  final VoidCallback? onShowReceipt;

  const _BillShareCard({
    required this.share,
    required this.onOpenHistory,
    this.onPay,
    this.onDispute,
    this.onShowReceipt,
  });

  @override
  Widget build(BuildContext context) {
    final latestDispute = share.latestDispute;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
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
                        share.bill.displayTitle,
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${share.split.splitMethod.displayName} • Due ${_formatDate(share.bill.dueDate)}',
                      ),
                    ],
                  ),
                ),
                _StatusBadge(
                  label: share.split.status.displayName,
                  color: _billShareStatusColor(context, share.split.status),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _AmountChip(
                  label: 'Share',
                  value: _formatCurrency(share.split.assignedAmount, 'NPR'),
                ),
                _AmountChip(
                  label: 'Paid',
                  value: _formatCurrency(share.split.paidAmount, 'NPR'),
                ),
                _AmountChip(
                  label: 'Outstanding',
                  value: _formatCurrency(share.split.outstandingAmount, 'NPR'),
                  emphasize: share.split.outstandingAmount > 0.01,
                ),
              ],
            ),
            if (latestDispute != null) ...[
              const SizedBox(height: 12),
              Text(
                '${latestDispute.status.displayName} dispute: ${latestDispute.reason}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(
                  onPressed: onOpenHistory,
                  icon: const Icon(Icons.history_outlined),
                  label: const Text('History'),
                ),
                if (onShowReceipt != null)
                  OutlinedButton.icon(
                    onPressed: onShowReceipt,
                    icon: const Icon(Icons.receipt_long_outlined),
                    label: const Text('Receipt'),
                  ),
                if (onDispute != null)
                  OutlinedButton.icon(
                    onPressed: onDispute,
                    icon: const Icon(Icons.report_gmailerrorred_outlined),
                    label: const Text('Dispute'),
                  ),
                if (onPay != null)
                  FilledButton.icon(
                    onPressed: onPay,
                    icon: const Icon(Icons.payment_outlined),
                    label: const Text('Pay share'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _TransactionHistorySection extends ConsumerWidget {
  final AsyncValue<List<PaymentTransaction>> transactionsAsync;

  const _TransactionHistorySection({required this.transactionsAsync});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return transactionsAsync.when(
      loading: () => const _SectionLoading(),
      error: (error, _) => _SectionErrorCard(
        message: ErrorHandler.handle(error).message,
        onRetry: () => ref.invalidate(transactionsProvider),
      ),
      data: (transactions) {
        if (transactions.isEmpty) {
          return const _SectionEmptyCard(
            icon: Icons.payments_outlined,
            title: 'No transactions recorded yet',
            subtitle:
                'Checkout attempts and completed payments will appear here once you start settling invoices or utility shares.',
          );
        }

        return Column(
          children: transactions
              .map((transaction) => _TransactionTile(transaction: transaction))
              .toList(),
        );
      },
    );
  }
}

class _TransactionTile extends StatelessWidget {
  final PaymentTransaction transaction;

  const _TransactionTile({required this.transaction});

  @override
  Widget build(BuildContext context) {
    final color = _paymentStatusColor(context, transaction.status);
    final amount = _displayTransactionAmount(transaction);
    final orderTitle = transaction.purchaseOrderName.trim().isNotEmpty
        ? transaction.purchaseOrderName
        : transaction.purchaseOrderId;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withValues(alpha: 0.12),
          child: Icon(Icons.payments_outlined, color: color),
        ),
        title: Text(
          orderTitle,
          style: const TextStyle(fontWeight: FontWeight.w600),
        ),
        subtitle: Text(
          '${transaction.provider.displayName} • ${transaction.purchaseOrderId}',
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              _formatCurrency(amount, transaction.currency.toUpperCase()),
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 4),
            _StatusBadge(label: transaction.status.name, color: color),
          ],
        ),
      ),
    );
  }
}

class _SheetScaffold extends StatelessWidget {
  final String title;
  final Widget child;

  const _SheetScaffold({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
          child: Text(
            title,
            style: Theme.of(context)
                .textTheme
                .titleLarge
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
        ),
        const Divider(height: 1),
        Expanded(child: child),
      ],
    );
  }
}

class _SheetLoading extends StatelessWidget {
  final String title;

  const _SheetLoading({required this.title});

  @override
  Widget build(BuildContext context) {
    return _SheetScaffold(
      title: title,
      child: const Center(child: CircularProgressIndicator.adaptive()),
    );
  }
}

class _SheetError extends StatelessWidget {
  final String title;
  final String message;
  final VoidCallback onRetry;

  const _SheetError({
    required this.title,
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return _SheetScaffold(
      title: title,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            const SizedBox(height: 12),
            FilledButton.tonalIcon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: const Text('Try again'),
            ),
          ],
        ),
      ),
    );
  }
}

class _InvoiceDetailSheet extends StatelessWidget {
  final InvoiceSummary invoice;
  final VoidCallback? onPay;
  final VoidCallback? onShowReceipt;
  final VoidCallback? onShowLedger;

  const _InvoiceDetailSheet({
    required this.invoice,
    this.onPay,
    this.onShowReceipt,
    this.onShowLedger,
  });

  @override
  Widget build(BuildContext context) {
    return _SheetScaffold(
      title: invoice.displayTitle,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _StatusBadge(
                label: invoice.status.displayName,
                color: _invoiceStatusColor(context, invoice.status),
              ),
              _StatusBadge(
                label: invoice.invoiceType.displayName,
                color: Colors.indigo,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _AmountChip(
                label: 'Subtotal',
                value: _formatCurrency(invoice.subtotal, invoice.currency),
              ),
              _AmountChip(
                label: 'Tax',
                value: _formatCurrency(invoice.taxAmount, invoice.currency),
              ),
              _AmountChip(
                label: 'Outstanding',
                value: _formatCurrency(
                    invoice.outstandingAmount, invoice.currency),
                emphasize: invoice.outstandingAmount > 0.01,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text('Due: ${_formatDate(invoice.dueDate)}'),
          const SizedBox(height: 4),
          Text(
              'Period: ${_formatPeriod(invoice.periodStart, invoice.periodEnd)}'),
          const SizedBox(height: 20),
          Text(
            'Line items',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (invoice.lineItems.isEmpty)
            const Text('No line items were attached to this invoice.')
          else
            ...invoice.lineItems.map(
              (item) => ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(item.description),
                subtitle: Text(item.lineItemType.replaceAll('_', ' ')),
                trailing: Text(
                  _formatCurrency(
                      item.amount + item.taxAmount, invoice.currency),
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
            ),
          const SizedBox(height: 20),
          Text(
            'Payments',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (invoice.payments.isEmpty)
            const Text(
                'No successful or pending payments have been recorded yet.')
          else
            ...invoice.payments.map(
              (payment) => ListTile(
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(
                  radius: 18,
                  backgroundColor: _paymentStatusColor(context, payment.status)
                      .withValues(alpha: 0.12),
                  child: Icon(
                    Icons.payments_outlined,
                    size: 18,
                    color: _paymentStatusColor(context, payment.status),
                  ),
                ),
                title: Text(payment.paymentMethod.displayName),
                subtitle: Text(
                  payment.createdAt == null
                      ? payment.status.name
                      : '${payment.status.name} • ${_formatDate(payment.createdAt)}',
                ),
                trailing: Text(
                  _formatCurrency(payment.amount, payment.currency),
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ),
            ),
          const SizedBox(height: 20),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (onShowLedger != null)
                OutlinedButton.icon(
                  onPressed: onShowLedger,
                  icon: const Icon(Icons.timeline_outlined),
                  label: const Text('Open ledger'),
                ),
              if (onShowReceipt != null)
                OutlinedButton.icon(
                  onPressed: onShowReceipt,
                  icon: const Icon(Icons.receipt_long_outlined),
                  label: const Text('Open receipt'),
                ),
              if (onPay != null)
                FilledButton.icon(
                  onPressed: onPay,
                  icon: const Icon(Icons.payment_outlined),
                  label: const Text('Pay invoice'),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _RentLedgerSheet extends StatelessWidget {
  final String title;
  final RentLedger ledger;
  final void Function(AdditionalChargeSummary charge)? onDisputeCharge;

  const _RentLedgerSheet({
    required this.title,
    required this.ledger,
    this.onDisputeCharge,
  });

  @override
  Widget build(BuildContext context) {
    return _SheetScaffold(
      title: title,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _AmountChip(
                label: 'Total scheduled',
                value: _formatCurrency(ledger.totalAmount, ledger.currency),
              ),
              _AmountChip(
                label: 'Paid',
                value: _formatCurrency(ledger.paidAmount, ledger.currency),
              ),
              _AmountChip(
                label: 'Outstanding',
                value:
                    _formatCurrency(ledger.outstandingAmount, ledger.currency),
                emphasize: ledger.outstandingAmount > 0.01,
              ),
            ],
          ),
          const SizedBox(height: 20),
          Text(
            'Schedule',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (ledger.entries.isEmpty)
            const Text('No rent periods have been scheduled yet.')
          else
            ...ledger.entries.map(
              (entry) => Card(
                margin: const EdgeInsets.only(bottom: 10),
                child: Padding(
                  padding: const EdgeInsets.all(12),
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
                                  _formatPeriod(
                                      entry.periodStart, entry.periodEnd),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text('Due ${_formatDate(entry.dueDate)}'),
                              ],
                            ),
                          ),
                          if (entry.invoiceStatus != null)
                            _StatusBadge(
                              label: entry.invoiceStatus!.displayName,
                              color: _invoiceStatusColor(
                                context,
                                entry.invoiceStatus!,
                              ),
                            ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          _AmountChip(
                            label: 'Due',
                            value: _formatCurrency(
                                entry.amountDue, ledger.currency),
                          ),
                          _AmountChip(
                            label: 'Paid',
                            value: _formatCurrency(
                                entry.paidAmount, ledger.currency),
                          ),
                          _AmountChip(
                            label: 'Outstanding',
                            value: _formatCurrency(
                              entry.outstandingAmount,
                              ledger.currency,
                            ),
                            emphasize: entry.outstandingAmount > 0.01,
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          if (ledger.additionalCharges.isNotEmpty) ...[
            const SizedBox(height: 20),
            Text(
              'Additional charges',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...ledger.additionalCharges.map(
              (charge) {
                final canDispute = !const ['paid', 'waived', 'disputed']
                    .contains(charge.status.toLowerCase());

                return Card(
                  margin: const EdgeInsets.only(bottom: 10),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
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
                                    charge.description,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(charge.displayStatus),
                                  if (charge.disputeReason.isNotEmpty) ...[
                                    const SizedBox(height: 6),
                                    Text('Dispute: ${charge.disputeReason}'),
                                  ],
                                  if (charge.resolutionNotes.isNotEmpty) ...[
                                    const SizedBox(height: 4),
                                    Text(
                                      'Resolution: ${charge.resolutionNotes}',
                                    ),
                                  ],
                                ],
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text(
                              _formatCurrency(charge.amount, ledger.currency),
                              style:
                                  const TextStyle(fontWeight: FontWeight.w600),
                            ),
                          ],
                        ),
                        if (canDispute && onDisputeCharge != null) ...[
                          const SizedBox(height: 12),
                          OutlinedButton.icon(
                            onPressed: () => onDisputeCharge?.call(charge),
                            icon: const Icon(Icons.report_gmailerrorred_outlined),
                            label: const Text('Dispute charge'),
                          ),
                        ],
                      ],
                    ),
                  ),
                );
              },
            ),
          ],
        ],
      ),
    );
  }
}

class _ReceiptSheet extends StatelessWidget {
  final String title;
  final String receipt;

  const _ReceiptSheet({required this.title, required this.receipt});

  @override
  Widget build(BuildContext context) {
    return _SheetScaffold(
      title: title,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SelectableText(
            receipt.trim().isEmpty
                ? 'Receipt content is unavailable.'
                : receipt,
            style:
                Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.4),
          ),
        ],
      ),
    );
  }
}

class _UtilityBillHistorySheet extends StatelessWidget {
  final UtilityBillShare share;
  final UtilityBillHistory history;
  final VoidCallback? onPay;
  final VoidCallback? onDispute;
  final VoidCallback? onShowReceipt;
  final Future<void> Function(String url) onOpenAttachment;

  const _UtilityBillHistorySheet({
    required this.share,
    required this.history,
    this.onPay,
    this.onDispute,
    this.onShowReceipt,
    required this.onOpenAttachment,
  });

  @override
  Widget build(BuildContext context) {
    return _SheetScaffold(
      title: share.bill.displayTitle,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _StatusBadge(
                label: share.split.status.displayName,
                color: _billShareStatusColor(context, share.split.status),
              ),
              _StatusBadge(
                label: share.bill.status.displayName,
                color: Colors.indigo,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _AmountChip(
                label: 'Share',
                value: _formatCurrency(share.split.assignedAmount, 'NPR'),
              ),
              _AmountChip(
                label: 'Paid',
                value: _formatCurrency(share.split.paidAmount, 'NPR'),
              ),
              _AmountChip(
                label: 'Outstanding',
                value: _formatCurrency(share.split.outstandingAmount, 'NPR'),
                emphasize: share.split.outstandingAmount > 0.01,
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text('Due: ${_formatDate(share.bill.dueDate)}'),
          const SizedBox(height: 4),
          Text('Split: ${share.split.splitMethod.displayName}'),
          if (share.bill.notes.trim().isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(share.bill.notes),
          ],
          if (share.disputes.isNotEmpty) ...[
            const SizedBox(height: 20),
            Text(
              'Disputes',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...share.disputes.map(
              (dispute) => ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(dispute.status.displayName),
                subtitle: Text(dispute.reason),
                trailing: Text(_formatDate(dispute.openedAt)),
              ),
            ),
          ],
          if (share.bill.attachments.isNotEmpty) ...[
            const SizedBox(height: 20),
            Text(
              'Attachments',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            ...share.bill.attachments.map(
              (attachment) => ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const Icon(Icons.attach_file_outlined),
                title: Text(attachment.fileType),
                subtitle: Text(_formatDate(attachment.uploadedAt)),
                trailing: IconButton(
                  icon: const Icon(Icons.open_in_new_outlined),
                  onPressed: () => onOpenAttachment(attachment.fileUrl),
                ),
              ),
            ),
          ],
          const SizedBox(height: 20),
          Text(
            'History',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          if (history.entries.isEmpty)
            const Text('No bill events are available yet.')
          else
            ...history.entries.map(
              (entry) => Card(
                margin: const EdgeInsets.only(bottom: 10),
                child: ListTile(
                  title: Text(entry.displayTitle),
                  subtitle: Text(entry.message),
                  trailing: Text(
                    _formatDate(entry.occurredAt),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              ),
            ),
          const SizedBox(height: 20),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (onShowReceipt != null)
                OutlinedButton.icon(
                  onPressed: onShowReceipt,
                  icon: const Icon(Icons.receipt_long_outlined),
                  label: const Text('Open receipt'),
                ),
              if (onDispute != null)
                OutlinedButton.icon(
                  onPressed: onDispute,
                  icon: const Icon(Icons.report_gmailerrorred_outlined),
                  label: const Text('Raise dispute'),
                ),
              if (onPay != null)
                FilledButton.icon(
                  onPressed: onPay,
                  icon: const Icon(Icons.payment_outlined),
                  label: const Text('Pay share'),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _BillingCheckoutSheet extends ConsumerStatefulWidget {
  final String title;
  final String description;
  final String currency;
  final double outstandingAmount;
  final bool allowPartial;

  const _BillingCheckoutSheet({
    required this.title,
    required this.description,
    required this.currency,
    required this.outstandingAmount,
    required this.allowPartial,
  });

  @override
  ConsumerState<_BillingCheckoutSheet> createState() =>
      _BillingCheckoutSheetState();
}

class _BillingCheckoutSheetState extends ConsumerState<_BillingCheckoutSheet> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  PaymentProvider? _selectedProvider;
  bool _useCustomAmount = false;

  @override
  void dispose() {
    _amountController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final providersAsync = ref.watch(paymentProvidersProvider);

    return _SheetScaffold(
      title: widget.title,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(widget.description),
          const SizedBox(height: 12),
          Text(
            'Outstanding: ${_formatCurrency(widget.outstandingAmount, widget.currency)}',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 20),
          Text(
            'Provider',
            style: Theme.of(context)
                .textTheme
                .titleSmall
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          providersAsync.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: CircularProgressIndicator.adaptive(),
            ),
            error: (error, _) => Text(
              ErrorHandler.handle(error).message,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
            data: (providers) {
              final available = providers
                  .map(PaymentProvider.fromString)
                  .toSet()
                  .toList(growable: false);
              final selected = _selectedProvider ??
                  (available.isNotEmpty ? available.first : null);

              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (available.isEmpty)
                    const Text('No payment providers are available right now.'),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: available
                        .map(
                          (provider) => ChoiceChip(
                            label: Text(provider.displayName),
                            selected: selected == provider,
                            onSelected: (_) =>
                                setState(() => _selectedProvider = provider),
                          ),
                        )
                        .toList(),
                  ),
                  if (selected == PaymentProvider.khalti) ...[
                    const SizedBox(height: 12),
                    _CredentialHint(
                      color: Colors.blue.shade50,
                      borderColor: Colors.blue.shade200,
                      title: 'Khalti sandbox',
                      lines: const [
                        'Mobile: 9800000000 – 9800000005',
                        'MPIN: 1111  ·  OTP: 987654',
                        'Amounts are sent in paisa behind the scenes.',
                      ],
                    ),
                  ],
                  if (selected == PaymentProvider.esewa) ...[
                    const SizedBox(height: 12),
                    _CredentialHint(
                      color: Colors.green.shade50,
                      borderColor: Colors.green.shade200,
                      title: 'eSewa sandbox',
                      lines: const [
                        'ID: 9806800001 – 9806800005',
                        'Password: Nepal@123  ·  OTP: 123456',
                        'Amounts are sent in NPR.',
                      ],
                    ),
                  ],
                ],
              );
            },
          ),
          const SizedBox(height: 20),
          if (widget.allowPartial) ...[
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              value: _useCustomAmount,
              title: const Text('Pay a custom amount'),
              subtitle: const Text(
                'Use the partial-payment flow to settle part of the invoice now.',
              ),
              onChanged: (value) => setState(() => _useCustomAmount = value),
            ),
            if (_useCustomAmount) ...[
              const SizedBox(height: 8),
              Form(
                key: _formKey,
                child: TextFormField(
                  controller: _amountController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Amount (${widget.currency})',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.payments_outlined),
                    helperText:
                        'Enter up to ${_formatCurrency(widget.outstandingAmount, widget.currency)}',
                  ),
                  validator: (value) {
                    final parsed = double.tryParse(value?.trim() ?? '');
                    if (parsed == null || parsed <= 0) {
                      return 'Enter a valid amount.';
                    }
                    if (parsed > widget.outstandingAmount + 0.01) {
                      return 'Amount cannot exceed the outstanding balance.';
                    }
                    return null;
                  },
                ),
              ),
            ],
          ] else
            const Text(
              'This bill-share checkout uses the full published amount.',
            ),
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: providersAsync.hasValue &&
                    providersAsync.value!.isNotEmpty
                ? () {
                    final selected = _selectedProvider ??
                        PaymentProvider.fromString(providersAsync.value!.first);
                    if (_useCustomAmount &&
                        !(_formKey.currentState?.validate() ?? false)) {
                      return;
                    }
                    Navigator.of(context).pop(
                      _BillingCheckoutSelection(
                        provider: selected,
                        amount: _useCustomAmount
                            ? double.tryParse(_amountController.text.trim())
                            : null,
                      ),
                    );
                  }
                : null,
            icon: const Icon(Icons.open_in_new_outlined),
            label: Text(
              providersAsync.hasValue && providersAsync.value!.isNotEmpty
                  ? 'Continue to checkout'
                  : 'Provider unavailable',
            ),
          ),
        ],
      ),
    );
  }
}

class _CredentialHint extends StatelessWidget {
  final Color color;
  final Color borderColor;
  final String title;
  final List<String> lines;

  const _CredentialHint({
    required this.color,
    required this.borderColor,
    required this.title,
    required this.lines,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
          ),
          const SizedBox(height: 2),
          ...lines
              .map((line) => Text(line, style: const TextStyle(fontSize: 11))),
        ],
      ),
    );
  }
}
