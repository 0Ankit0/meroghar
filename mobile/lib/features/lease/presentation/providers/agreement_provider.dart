import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../applications/application_access.dart';
import '../../data/models/lease_agreement.dart';
import '../../data/repositories/agreement_repository.dart';

final agreementRepositoryProvider = Provider<AgreementRepository>((ref) {
  return AgreementRepository(ref.watch(dioClientProvider));
});

final bookingAgreementProvider =
    FutureProvider.family<LeaseAgreement?, String>((ref, bookingId) {
  final authState = ref.watch(authNotifierProvider).valueOrNull;
  if (authState?.isAuthenticated != true) {
    return null;
  }
  return ref.watch(agreementRepositoryProvider).getAgreement(bookingId);
});

final canManageAgreementsProvider = Provider<bool>((ref) {
  final roles = ref.watch(authNotifierProvider).valueOrNull?.user?.roles ??
      const <String>[];
  return canManageAgreements(roles);
});

final canSignAgreementProvider = Provider<bool>((ref) {
  final roles = ref.watch(authNotifierProvider).valueOrNull?.user?.roles ??
      const <String>[];
  return canSignLeaseAgreement(roles);
});
