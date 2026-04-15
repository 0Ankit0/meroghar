import '../../../../core/error/app_exception.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/utils/json_parsing.dart';
import '../models/lease_agreement.dart';

class AgreementRepository {
  final DioClient _dioClient;

  AgreementRepository(this._dioClient);

  Future<LeaseAgreement?> getAgreement(String bookingId) async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.bookingAgreement(bookingId));
      final map = _extractMap(response.data);
      if (map.isEmpty) return null;
      return LeaseAgreement.fromJson(map);
    } catch (e) {
      final handled = ErrorHandler.handle(e);
      if (handled is ServerException && handled.statusCode == 404) {
        return null;
      }
      throw handled;
    }
  }

  Future<void> generateAgreement(
    String bookingId, {
    String? templateId,
  }) async {
    await _postAction(
      ApiEndpoints.bookingAgreement(bookingId),
      data: templateId != null && templateId.trim().isNotEmpty
          ? {'templateId': templateId.trim()}
          : null,
    );
  }

  Future<void> sendAgreement(String bookingId) async {
    await _postAction(ApiEndpoints.bookingAgreementSend(bookingId));
  }

  Future<void> countersignAgreement(String bookingId) async {
    await _postAction(ApiEndpoints.bookingAgreementCountersign(bookingId));
  }

  Future<void> _postAction(
    String endpoint, {
    Map<String, dynamic>? data,
  }) async {
    try {
      await _dioClient.dio.post(
        endpoint,
        data: data == null || data.isEmpty ? null : data,
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  dynamic _extractData(dynamic payload) {
    final map = asJsonMap(payload);
    if (map.containsKey('data')) return map['data'];
    return payload;
  }

  Map<String, dynamic> _extractMap(dynamic payload) {
    final extracted = _extractData(payload);
    final extractedMap = asJsonMap(extracted);
    if (extractedMap.isNotEmpty) return extractedMap;
    return asJsonMap(payload);
  }
}
