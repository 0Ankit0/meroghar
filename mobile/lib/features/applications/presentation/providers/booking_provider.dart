import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/providers/dio_provider.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../application_access.dart';
import '../../data/models/booking.dart';
import '../../data/repositories/booking_repository.dart';

final bookingRepositoryProvider = Provider<BookingRepository>((ref) {
  return BookingRepository(ref.watch(dioClientProvider));
});

final bookingsProvider = FutureProvider<List<BookingRecord>>((ref) {
  final authState = ref.watch(authNotifierProvider).valueOrNull;
  if (authState?.isAuthenticated != true) {
    return const <BookingRecord>[];
  }
  return ref.watch(bookingRepositoryProvider).getBookings();
});

final bookingDetailProvider =
    FutureProvider.family<BookingRecord, String>((ref, bookingId) {
  return ref.watch(bookingRepositoryProvider).getBookingDetail(bookingId);
});

final bookingEventsProvider =
    FutureProvider.family<List<BookingEvent>, String>((ref, bookingId) {
  return ref.watch(bookingRepositoryProvider).getBookingEvents(bookingId);
});

final canViewApplicationsProvider = Provider<bool>((ref) {
  final roles = ref.watch(authNotifierProvider).valueOrNull?.user?.roles ??
      const <String>[];
  return canViewApplications(roles);
});

final canSubmitApplicationsProvider = Provider<bool>((ref) {
  final roles = ref.watch(authNotifierProvider).valueOrNull?.user?.roles ??
      const <String>[];
  return canSubmitApplications(roles);
});

final canManageApplicationsProvider = Provider<bool>((ref) {
  final roles = ref.watch(authNotifierProvider).valueOrNull?.user?.roles ??
      const <String>[];
  return canManageApplications(roles);
});
