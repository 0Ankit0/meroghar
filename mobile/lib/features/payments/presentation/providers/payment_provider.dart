import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../data/models/billing.dart';
import '../../data/models/payment.dart';
import '../../data/repositories/payment_repository.dart';

final paymentRepositoryProvider = Provider<PaymentRepository>((ref) {
  return PaymentRepository(ref.watch(dioClientProvider));
});

final paymentProvidersProvider = FutureProvider<List<String>>((ref) {
  return ref.watch(paymentRepositoryProvider).getProviders();
});

final transactionsProvider = FutureProvider<List<PaymentTransaction>>((ref) {
  final authState = ref.watch(authNotifierProvider).valueOrNull;
  if (authState?.isAuthenticated != true) {
    return const <PaymentTransaction>[];
  }
  return ref.watch(paymentRepositoryProvider).getTransactions();
});

final invoicesProvider = FutureProvider<List<InvoiceSummary>>((ref) {
  final authState = ref.watch(authNotifierProvider).valueOrNull;
  if (authState?.isAuthenticated != true) {
    return const <InvoiceSummary>[];
  }
  return ref.watch(paymentRepositoryProvider).getInvoices();
});

final invoiceDetailProvider =
    FutureProvider.family<InvoiceSummary, String>((ref, invoiceId) {
  return ref.watch(paymentRepositoryProvider).getInvoiceDetail(invoiceId);
});

final invoiceReceiptProvider =
    FutureProvider.family<String, String>((ref, invoiceId) {
  return ref.watch(paymentRepositoryProvider).getInvoiceReceipt(invoiceId);
});

final rentLedgerProvider =
    FutureProvider.family<RentLedger, String>((ref, bookingId) {
  return ref.watch(paymentRepositoryProvider).getRentLedger(bookingId);
});

final tenantBillSharesProvider = FutureProvider<List<UtilityBillShare>>((ref) {
  final authState = ref.watch(authNotifierProvider).valueOrNull;
  if (authState?.isAuthenticated != true) {
    return const <UtilityBillShare>[];
  }
  return ref.watch(paymentRepositoryProvider).getTenantBillShares();
});

final utilityBillHistoryProvider =
    FutureProvider.family<UtilityBillHistory, String>((ref, billId) {
  return ref.watch(paymentRepositoryProvider).getUtilityBillHistory(billId);
});
