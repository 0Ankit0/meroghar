/// Secure storage service for JWT tokens and sensitive data.
/// Implements T020 from tasks.md.
library;

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../config/env.example.dart';

/// Service for securely storing sensitive data like JWT tokens.
/// 
/// Uses platform-specific secure storage:
/// - iOS: Keychain
/// - Android: EncryptedSharedPreferences
class SecureStorageService {
  static final SecureStorageService instance = SecureStorageService._internal();
  
  late final FlutterSecureStorage _storage;

  factory SecureStorageService() => instance;

  SecureStorageService._internal() {
    _storage = const FlutterSecureStorage(
      aOptions: AndroidOptions(
        encryptedSharedPreferences: true,
      ),
      iOptions: IOSOptions(
        accessibility: KeychainAccessibility.first_unlock_this_device,
      ),
    );
  }

  /// Generate storage key with prefix.
  String _key(String key) => '${Environment.secureStoragePrefix}$key';

  // ==================== Token Management ====================

  /// Save access token.
  Future<void> saveAccessToken(String token) async {
    await _storage.write(
      key: _key(Environment.accessTokenKey),
      value: token,
    );
  }

  /// Get access token.
  Future<String?> getAccessToken() async {
    return await _storage.read(key: _key(Environment.accessTokenKey));
  }

  /// Delete access token.
  Future<void> deleteAccessToken() async {
    await _storage.delete(key: _key(Environment.accessTokenKey));
  }

  /// Save refresh token.
  Future<void> saveRefreshToken(String token) async {
    await _storage.write(
      key: _key(Environment.refreshTokenKey),
      value: token,
    );
  }

  /// Get refresh token.
  Future<String?> getRefreshToken() async {
    return await _storage.read(key: _key(Environment.refreshTokenKey));
  }

  /// Delete refresh token.
  Future<void> deleteRefreshToken() async {
    await _storage.delete(key: _key(Environment.refreshTokenKey));
  }

  /// Save both access and refresh tokens.
  Future<void> saveTokens({
    required String accessToken,
    required String refreshToken,
  }) async {
    await Future.wait([
      saveAccessToken(accessToken),
      saveRefreshToken(refreshToken),
    ]);
  }

  /// Delete both access and refresh tokens.
  Future<void> deleteTokens() async {
    await Future.wait([
      deleteAccessToken(),
      deleteRefreshToken(),
    ]);
  }

  /// Check if user has valid tokens stored.
  Future<bool> hasTokens() async {
    final accessToken = await getAccessToken();
    final refreshToken = await getRefreshToken();
    return accessToken != null && refreshToken != null;
  }

  // ==================== User Data ====================

  /// Save user ID.
  Future<void> saveUserId(String userId) async {
    await _storage.write(
      key: _key(Environment.userIdKey),
      value: userId,
    );
  }

  /// Get user ID.
  Future<String?> getUserId() async {
    return await _storage.read(key: _key(Environment.userIdKey));
  }

  /// Delete user ID.
  Future<void> deleteUserId() async {
    await _storage.delete(key: _key(Environment.userIdKey));
  }

  // ==================== Generic Storage ====================

  /// Save any string value securely.
  Future<void> saveString(String key, String value) async {
    await _storage.write(
      key: _key(key),
      value: value,
    );
  }

  /// Read any string value.
  Future<String?> readString(String key) async {
    return await _storage.read(key: _key(key));
  }

  /// Delete any value.
  Future<void> delete(String key) async {
    await _storage.delete(key: _key(key));
  }

  /// Check if key exists.
  Future<bool> containsKey(String key) async {
    final value = await _storage.read(key: _key(key));
    return value != null;
  }

  // ==================== Bulk Operations ====================

  /// Get all stored keys.
  Future<Map<String, String>> readAll() async {
    return await _storage.readAll();
  }

  /// Delete all stored values (logout).
  Future<void> deleteAll() async {
    await _storage.deleteAll();
  }

  /// Clear all app-specific data (keeps other app data).
  Future<void> clearAppData() async {
    final allData = await readAll();
    final appKeys = allData.keys.where(
      (key) => key.startsWith(Environment.secureStoragePrefix),
    );

    await Future.wait(
      appKeys.map((key) => _storage.delete(key: key)),
    );
  }

  // ==================== Session Management ====================

  /// Save complete authentication session.
  Future<void> saveAuthSession({
    required String accessToken,
    required String refreshToken,
    required String userId,
  }) async {
    await Future.wait([
      saveAccessToken(accessToken),
      saveRefreshToken(refreshToken),
      saveUserId(userId),
    ]);
  }

  /// Load complete authentication session.
  Future<AuthSession?> loadAuthSession() async {
    final results = await Future.wait([
      getAccessToken(),
      getRefreshToken(),
      getUserId(),
    ]);

    final accessToken = results[0] as String?;
    final refreshToken = results[1] as String?;
    final userId = results[2] as String?;

    if (accessToken == null || refreshToken == null || userId == null) {
      return null;
    }

    return AuthSession(
      accessToken: accessToken,
      refreshToken: refreshToken,
      userId: userId,
    );
  }

  /// Clear authentication session (logout).
  Future<void> clearAuthSession() async {
    await Future.wait([
      deleteAccessToken(),
      deleteRefreshToken(),
      deleteUserId(),
    ]);
  }
}

/// Authentication session data model.
class AuthSession {
  final String accessToken;
  final String refreshToken;
  final String userId;

  const AuthSession({
    required this.accessToken,
    required this.refreshToken,
    required this.userId,
  });

  Map<String, dynamic> toJson() => {
        'accessToken': accessToken,
        'refreshToken': refreshToken,
        'userId': userId,
      };

  factory AuthSession.fromJson(Map<String, dynamic> json) {
    return AuthSession(
      accessToken: json['accessToken'] as String,
      refreshToken: json['refreshToken'] as String,
      userId: json['userId'] as String,
    );
  }
}
