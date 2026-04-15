import 'package:dio/dio.dart';
import '../../../../core/error/app_exception.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/utils/json_parsing.dart';
import '../models/booking.dart';
import '../models/create_booking_request.dart';

class BookingRepository {
  final DioClient _dioClient;

  BookingRepository(this._dioClient);

  Future<List<BookingRecord>> getBookings() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.bookings);
      final rawBookings = _extractList(
        response.data,
        collectionKeys: const ['bookings', 'items', 'results'],
      );
      final bookings = rawBookings
          .map((item) => BookingRecord.fromJson(asJsonMap(item)))
          .where((item) => item.id.isNotEmpty || item.bookingNumber.isNotEmpty)
          .toList()
        ..sort((a, b) {
          final aTime = a.createdAt ?? a.updatedAt;
          final bTime = b.createdAt ?? b.updatedAt;
          if (aTime == null && bTime == null) return 0;
          if (aTime == null) return 1;
          if (bTime == null) return -1;
          return bTime.compareTo(aTime);
        });
      return bookings;
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<BookingRecord> getBookingDetail(String bookingId) async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.bookingById(bookingId));
      return BookingRecord.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<BookingRecord> createBooking(CreateBookingRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.bookings,
        data: request.toJson(),
        options: Options(headers: request.toHeaders()),
      );
      return BookingRecord.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> confirmBooking(String bookingId) async {
    await _postAction(ApiEndpoints.bookingConfirm(bookingId));
  }

  Future<void> declineBooking(String bookingId, {String? reason}) async {
    await _postAction(
      ApiEndpoints.bookingDecline(bookingId),
      body: _reasonPayload(reason),
    );
  }

  Future<void> cancelBooking(String bookingId, {String? reason}) async {
    await _postAction(
      ApiEndpoints.bookingCancel(bookingId),
      body: _reasonPayload(reason),
    );
  }

  Future<void> requestReturn(String bookingId) async {
    await _postAction(ApiEndpoints.bookingReturn(bookingId));
  }

  Future<List<BookingEvent>> getBookingEvents(String bookingId) async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.bookingEvents(bookingId));
      final rawEvents = _extractList(
        response.data,
        collectionKeys: const ['events', 'items', 'results'],
      );
      final events = rawEvents
          .map((item) => BookingEvent.fromJson(asJsonMap(item)))
          .toList()
        ..sort((a, b) {
          final aTime = a.createdAt;
          final bTime = b.createdAt;
          if (aTime == null && bTime == null) return 0;
          if (aTime == null) return 1;
          if (bTime == null) return -1;
          return aTime.compareTo(bTime);
        });
      return events;
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<void> _postAction(
    String endpoint, {
    Map<String, dynamic>? body,
  }) async {
    try {
      await _dioClient.dio.post(
        endpoint,
        data: body == null || body.isEmpty ? null : body,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Map<String, dynamic>? _reasonPayload(String? reason) {
    if (reason == null || reason.trim().isEmpty) return null;
    return {'reason': reason.trim()};
  }

  dynamic _extractData(dynamic payload) {
    final map = asJsonMap(payload);
    if (map.containsKey('data')) return map['data'];
    return payload;
  }

  List<dynamic> _extractList(
    dynamic payload, {
    Iterable<String> collectionKeys = const [],
  }) {
    final extracted = _extractData(payload);
    final extractedList = asJsonList(extracted);
    if (extractedList.isNotEmpty) return extractedList;

    final extractedMap = asJsonMap(extracted);
    for (final key in collectionKeys) {
      final collection = asJsonList(extractedMap[key]);
      if (collection.isNotEmpty) return collection;
    }

    final root = asJsonMap(payload);
    for (final key in collectionKeys) {
      final collection = asJsonList(root[key]);
      if (collection.isNotEmpty) return collection;
    }

    return const <dynamic>[];
  }

  Map<String, dynamic> _extractMap(dynamic payload) {
    final extracted = _extractData(payload);
    final extractedMap = asJsonMap(extracted);
    if (extractedMap.isNotEmpty) return extractedMap;
    return asJsonMap(payload);
  }

  Map<String, dynamic> _extractRequiredMap(dynamic payload) {
    final map = _extractMap(payload);
    if (map.isEmpty) {
      throw const ServerException(message: 'Unexpected response format.');
    }
    return map;
  }
}
