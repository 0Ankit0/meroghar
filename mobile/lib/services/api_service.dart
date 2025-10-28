/// Dio HTTP client with authentication interceptors.
/// Implements T021 from tasks.md.
library;

import 'dart:io';

import 'package:dio/dio.dart';

import '../config/env.example.dart';
import 'secure_storage_service.dart';

/// HTTP client service with automatic JWT authentication.
///
/// Features:
/// - Automatic access token injection
/// - Automatic token refresh on 401
/// - Error response parsing
/// - Request/response logging
/// - Timeout configuration
class ApiService {
  factory ApiService() => instance;

  ApiService._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: Environment.apiBaseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        validateStatus: (status) {
          // Consider all status codes as valid to handle them manually
          return status != null && status < 500;
        },
      ),
    );

    _setupInterceptors();
  }
  static final ApiService instance = ApiService._internal();

  late final Dio _dio;
  final SecureStorageService _storage = SecureStorageService.instance;

  bool _isRefreshing = false;
  final List<void Function()> _requestsWaitingForToken = [];

  /// Configure request/response interceptors.
  void _setupInterceptors() {
    // Request interceptor - add auth token
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Add access token if available
          final accessToken = await _storage.getAccessToken();
          if (accessToken != null) {
            options.headers['Authorization'] = 'Bearer $accessToken';
          }

          // Log request in debug mode
          if (Environment.apiLogRequests) {
            print('[API Request] ${options.method} ${options.path}');
            print('[API Headers] ${options.headers}');
            if (options.data != null) {
              print('[API Body] ${options.data}');
            }
          }

          handler.next(options);
        },
        onResponse: (response, handler) {
          // Log response in debug mode
          if (Environment.apiLogRequests) {
            print(
                '[API Response] ${response.statusCode} ${response.requestOptions.path}');
            print('[API Data] ${response.data}');
          }

          handler.next(response);
        },
        onError: (error, handler) async {
          // Handle 401 Unauthorized - attempt token refresh
          if (error.response?.statusCode == 401) {
            final refreshToken = await _storage.getRefreshToken();

            if (refreshToken != null && !_isRefreshing) {
              _isRefreshing = true;

              try {
                // Attempt to refresh token
                final newTokens = await _refreshToken(refreshToken);

                if (newTokens != null) {
                  // Save new tokens
                  await _storage.saveTokens(
                    accessToken: newTokens['access_token'] as String,
                    refreshToken: newTokens['refresh_token'] as String,
                  );

                  // Retry original request with new token
                  final options = error.requestOptions;
                  options.headers['Authorization'] =
                      'Bearer ${newTokens['access_token']}';

                  final response = await _dio.fetch(options);
                  handler.resolve(response);

                  // Execute waiting requests
                  _isRefreshing = false;
                  for (final callback in _requestsWaitingForToken) {
                    callback();
                  }
                  _requestsWaitingForToken.clear();
                  return;
                }
              } catch (e) {
                _isRefreshing = false;
                _requestsWaitingForToken.clear();

                // Clear session on refresh failure
                await _storage.clearAuthSession();
              }
            }
          }

          // Log error in debug mode
          if (Environment.apiLogRequests) {
            print(
                '[API Error] ${error.response?.statusCode} ${error.requestOptions.path}');
            print('[API Error Data] ${error.response?.data}');
          }

          handler.next(error);
        },
      ),
    );
  }

  /// Refresh access token using refresh token.
  Future<Map<String, dynamic>?> _refreshToken(String refreshToken) async {
    try {
      final response = await _dio.post(
        '/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
        options: Options(
          headers: {
            'Authorization': 'Bearer $refreshToken',
          },
        ),
      );

      if (response.statusCode == 200 && response.data['success'] == true) {
        return response.data['data'] as Map<String, dynamic>;
      }

      return null;
    } catch (e) {
      print('[API] Token refresh failed: $e');
      return null;
    }
  }

  // ==================== HTTP Methods ====================

  /// Perform GET request.
  Future<ApiResponse<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      final response = await _dio.get(
        path,
        queryParameters: queryParameters,
        options: options,
      );

      return _handleResponse<T>(response);
    } on DioException catch (e) {
      return _handleError<T>(e);
    }
  }

  /// Perform POST request.
  Future<ApiResponse<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      final response = await _dio.post(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );

      return _handleResponse<T>(response);
    } on DioException catch (e) {
      return _handleError<T>(e);
    }
  }

  /// Perform PUT request.
  Future<ApiResponse<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      final response = await _dio.put(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );

      return _handleResponse<T>(response);
    } on DioException catch (e) {
      return _handleError<T>(e);
    }
  }

  /// Perform PATCH request.
  Future<ApiResponse<T>> patch<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      final response = await _dio.patch(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );

      return _handleResponse<T>(response);
    } on DioException catch (e) {
      return _handleError<T>(e);
    }
  }

  /// Perform DELETE request.
  Future<ApiResponse<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      final response = await _dio.delete(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );

      return _handleResponse<T>(response);
    } on DioException catch (e) {
      return _handleError<T>(e);
    }
  }

  /// Upload file with multipart/form-data.
  Future<ApiResponse<T>> uploadFile<T>(
    String path,
    File file, {
    String fieldName = 'file',
    Map<String, dynamic>? data,
    ProgressCallback? onSendProgress,
  }) async {
    try {
      final formData = FormData.fromMap({
        fieldName: await MultipartFile.fromFile(
          file.path,
          filename: file.path.split('/').last,
        ),
        ...?data,
      });

      final response = await _dio.post(
        path,
        data: formData,
        onSendProgress: onSendProgress,
        options: Options(
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        ),
      );

      return _handleResponse<T>(response);
    } on DioException catch (e) {
      return _handleError<T>(e);
    }
  }

  /// Download file to local path.
  Future<ApiResponse<String>> downloadFile(
    String path,
    String savePath, {
    ProgressCallback? onReceiveProgress,
    Map<String, dynamic>? queryParameters,
  }) async {
    try {
      await _dio.download(
        path,
        savePath,
        onReceiveProgress: onReceiveProgress,
        queryParameters: queryParameters,
      );

      return ApiResponse<String>.success(savePath);
    } on DioException catch (e) {
      return _handleError<String>(e);
    }
  }

  // ==================== Response Handling ====================

  /// Handle successful response.
  ApiResponse<T> _handleResponse<T>(Response response) {
    if (response.statusCode != null &&
        response.statusCode! >= 200 &&
        response.statusCode! < 300) {
      final data = response.data;

      // Handle API success response format
      if (data is Map<String, dynamic> && data['success'] == true) {
        return ApiResponse<T>.success(
          data['data'] as T?,
          message: data['message'] as String?,
        );
      }

      // Handle raw response
      return ApiResponse<T>.success(data as T?);
    }

    // Handle error responses
    return _parseErrorResponse<T>(response);
  }

  /// Handle DioException error.
  ApiResponse<T> _handleError<T>(DioException error) {
    if (error.response != null) {
      return _parseErrorResponse<T>(error.response!);
    }

    // Network errors
    if (error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout ||
        error.type == DioExceptionType.sendTimeout) {
      return ApiResponse<T>.error(
        'Connection timeout. Please check your internet connection.',
        statusCode: 408,
      );
    }

    if (error.type == DioExceptionType.connectionError) {
      return ApiResponse<T>.error(
        'No internet connection. Please check your network.',
        statusCode: 0,
      );
    }

    return ApiResponse<T>.error(
      error.message ?? 'An unexpected error occurred.',
      statusCode: error.response?.statusCode,
    );
  }

  /// Parse error response from server.
  ApiResponse<T> _parseErrorResponse<T>(Response response) {
    final data = response.data;

    if (data is Map<String, dynamic>) {
      final message = data['detail'] as String? ??
          data['message'] as String? ??
          'An error occurred';

      final details = data['details'] as List<dynamic>?;

      return ApiResponse<T>.error(
        message,
        statusCode: response.statusCode,
        details: details?.map((e) => e.toString()).toList(),
      );
    }

    return ApiResponse<T>.error(
      'An error occurred',
      statusCode: response.statusCode,
    );
  }
}

/// API response wrapper.
class ApiResponse<T> {
  const ApiResponse({
    required this.success,
    this.data,
    this.message,
    this.statusCode,
    this.details,
  });

  factory ApiResponse.success(
    T? data, {
    String? message,
  }) {
    return ApiResponse<T>(
      success: true,
      data: data,
      message: message,
    );
  }

  factory ApiResponse.error(
    String message, {
    int? statusCode,
    List<String>? details,
  }) {
    return ApiResponse<T>(
      success: false,
      message: message,
      statusCode: statusCode,
      details: details,
    );
  }
  final bool success;
  final T? data;
  final String? message;
  final int? statusCode;
  final List<String>? details;

  /// Check if response is successful.
  bool get isSuccess => success && data != null;

  /// Check if response is error.
  bool get isError => !success;

  @override
  String toString() {
    if (success) {
      return 'ApiResponse.success(data: $data, message: $message)';
    } else {
      return 'ApiResponse.error(message: $message, statusCode: $statusCode, details: $details)';
    }
  }
}
