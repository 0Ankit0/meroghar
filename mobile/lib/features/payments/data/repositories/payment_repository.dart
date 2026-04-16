import 'package:dio/dio.dart';
import '../../../../core/error/app_exception.dart';
import '../../../../core/error/error_handler.dart';
import '../../../../core/network/api_endpoints.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/utils/json_parsing.dart';
import '../models/billing.dart';
import '../models/payment.dart';

class PaymentRepository {
  final DioClient _dioClient;

  PaymentRepository(this._dioClient);

  Future<List<String>> getProviders() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.paymentProviders);
      final list = _extractList(
        response.data,
        collectionKeys: const ['providers', 'items', 'results'],
      );
      return list
          .map((item) => item.toString().trim())
          .where((item) => item.isNotEmpty)
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<InitiatePaymentResponse> initiatePayment(
    InitiatePaymentRequest request,
  ) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.paymentInitiate,
        data: request.toJson(),
      );
      return InitiatePaymentResponse.fromJson(
        _extractRequiredMap(response.data),
      );
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<VerifyPaymentResponse> verifyPayment(
      VerifyPaymentRequest request) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.paymentVerify,
        data: request.toJson(),
      );
      return VerifyPaymentResponse.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<PaymentTransaction>> getTransactions() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.payments);
      final list = _extractList(
        response.data,
        collectionKeys: const ['transactions', 'items', 'results'],
      );
      return list
          .map((item) => PaymentTransaction.fromJson(asJsonMap(item)))
          .toList();
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<PaymentTransaction> getTransaction(String transactionId) async {
    try {
      final response = await _dioClient.dio.get(
        '${ApiEndpoints.payments}$transactionId/',
      );
      return PaymentTransaction.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<InvoiceSummary>> getInvoices() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.invoices);
      final payload =
          InvoiceListResponse.fromJson(_extractRequiredMap(response.data));
      return payload.items;
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<InvoiceSummary> getInvoiceDetail(String invoiceId) async {
    try {
      final response =
          await _dioClient.dio.get(ApiEndpoints.invoiceById(invoiceId));
      return InvoiceSummary.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<InitiatePaymentResponse> payInvoice(
    String invoiceId,
    BillingPaymentRequest request, {
    bool partial = false,
  }) async {
    try {
      final response = await _dioClient.dio.post(
        partial
            ? ApiEndpoints.invoicePartialPay(invoiceId)
            : ApiEndpoints.invoicePay(invoiceId),
        data: request.toJson(),
      );
      return InitiatePaymentResponse.fromJson(
          _extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<String> getInvoiceReceipt(String invoiceId) async {
    try {
      final response = await _dioClient.dio.get<String>(
        ApiEndpoints.invoiceReceipt(invoiceId),
        options: Options(responseType: ResponseType.plain),
      );
      final data = response.data;
      if (data != null && data.trim().isNotEmpty) return data;
      if (response.data is String) return response.data as String;
      return response.data?.toString() ?? '';
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<RentLedger> getRentLedger(String bookingId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.bookingRentLedger(bookingId),
      );
      return RentLedger.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<AdditionalChargeSummary> disputeAdditionalCharge(
    String chargeId,
    String reason,
  ) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.additionalChargeDispute(chargeId),
        data: {'reason': reason.trim()},
      );
      return AdditionalChargeSummary.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<List<UtilityBillShare>> getTenantBillShares() async {
    try {
      final response = await _dioClient.dio.get(ApiEndpoints.tenantBillShares);
      final payload = UtilityBillShareListResponse.fromJson(
        _extractRequiredMap(response.data),
      );
      return payload.items;
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<InitiatePaymentResponse> payBillShare(
    String billShareId,
    BillingPaymentRequest request,
  ) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.billSharePay(billShareId),
        data: request.toJson(),
      );
      return InitiatePaymentResponse.fromJson(
          _extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<UtilityBillDispute> disputeBillShare(
    String billShareId,
    BillShareDisputeRequest request,
  ) async {
    try {
      final response = await _dioClient.dio.post(
        ApiEndpoints.billShareDispute(billShareId),
        data: request.toJson(),
      );
      return UtilityBillDispute.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
  }

  Future<UtilityBillHistory> getUtilityBillHistory(String billId) async {
    try {
      final response = await _dioClient.dio.get(
        ApiEndpoints.utilityBillHistory(billId),
      );
      return UtilityBillHistory.fromJson(_extractRequiredMap(response.data));
    } catch (e) {
      throw ErrorHandler.handle(e);
    }
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
