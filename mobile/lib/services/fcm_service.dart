/// Firebase Cloud Messaging service for push notifications.
///
/// Implements T245 from tasks.md.
library;

import 'dart:async';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'api_service.dart';

/// Background message handler - must be top-level function
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('Handling background message: ${message.messageId}');
}

/// FCM Service for managing push notifications
class FCMService {
  factory FCMService() => _instance;
  FCMService._internal();
  static final FCMService _instance = FCMService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  final StreamController<RemoteMessage> _messageStreamController =
      StreamController<RemoteMessage>.broadcast();
  final StreamController<String> _tokenStreamController =
      StreamController<String>.broadcast();

  String? _currentToken;
  bool _initialized = false;

  /// Stream of foreground messages
  Stream<RemoteMessage> get messageStream => _messageStreamController.stream;

  /// Stream of token updates
  Stream<String> get tokenStream => _tokenStreamController.stream;

  /// Current FCM token
  String? get currentToken => _currentToken;

  /// Initialize FCM service
  Future<void> initialize() async {
    if (_initialized) {
      debugPrint('FCM already initialized');
      return;
    }

    try {
      // Request notification permissions
      final settings = await _requestPermissions();
      if (settings.authorizationStatus != AuthorizationStatus.authorized) {
        debugPrint('Notification permission not granted');
        return;
      }

      // Initialize local notifications
      await _initializeLocalNotifications();

      // Set up background message handler
      FirebaseMessaging.onBackgroundMessage(
          _firebaseMessagingBackgroundHandler);

      // Get FCM token
      _currentToken = await _messaging.getToken();
      if (_currentToken != null) {
        debugPrint('FCM Token: $_currentToken');
        _tokenStreamController.add(_currentToken!);
      }

      // Listen for token refresh
      _messaging.onTokenRefresh.listen((token) {
        _currentToken = token;
        debugPrint('FCM Token refreshed: $token');
        _tokenStreamController.add(token);
      });

      // Handle foreground messages
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

      // Handle notification taps when app is in background
      FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageTap);

      // Check if app was opened from a notification
      final initialMessage = await _messaging.getInitialMessage();
      if (initialMessage != null) {
        _handleMessageTap(initialMessage);
      }

      _initialized = true;
      debugPrint('FCM initialized successfully');
    } catch (e) {
      debugPrint('FCM initialization failed: $e');
      rethrow;
    }
  }

  /// Request notification permissions
  Future<NotificationSettings> _requestPermissions() async {
    final settings = await _messaging.requestPermission(
      alert: true,
      announcement: false,
      badge: true,
      carPlay: false,
      criticalAlert: false,
      provisional: false,
      sound: true,
    );

    debugPrint(
        'Notification permission status: ${settings.authorizationStatus}');
    return settings;
  }

  /// Initialize local notifications for foreground display
  Future<void> _initializeLocalNotifications() async {
    const androidSettings =
        AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: _handleLocalNotificationTap,
    );

    // Create notification channels for Android
    if (Platform.isAndroid) {
      await _createNotificationChannels();
    }
  }

  /// Create Android notification channels
  Future<void> _createNotificationChannels() async {
    const channels = [
      AndroidNotificationChannel(
        'urgent',
        'Urgent Notifications',
        description: 'High priority urgent notifications',
        importance: Importance.max,
        playSound: true,
        enableVibration: true,
      ),
      AndroidNotificationChannel(
        'payment_received',
        'Payment Notifications',
        description: 'Payment received notifications',
        importance: Importance.high,
        playSound: true,
      ),
      AndroidNotificationChannel(
        'bill_created',
        'Bill Notifications',
        description: 'New bill notifications',
        importance: Importance.high,
      ),
      AndroidNotificationChannel(
        'document_expiring',
        'Document Notifications',
        description: 'Document expiration notifications',
        importance: Importance.defaultImportance,
      ),
      AndroidNotificationChannel(
        'default',
        'General Notifications',
        description: 'General notifications',
        importance: Importance.defaultImportance,
      ),
    ];

    for (final channel in channels) {
      await _localNotifications
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(channel);
    }
  }

  /// Handle foreground messages
  void _handleForegroundMessage(RemoteMessage message) {
    debugPrint('Foreground message received: ${message.messageId}');

    // Add to stream for listeners
    _messageStreamController.add(message);

    // Show local notification
    _showLocalNotification(message);
  }

  /// Show local notification for foreground messages
  Future<void> _showLocalNotification(RemoteMessage message) async {
    final notification = message.notification;
    final android = message.notification?.android;
    final data = message.data;

    if (notification == null) return;

    // Determine channel based on notification type
    final notificationType = data['type'] ?? 'default';
    final priority = data['priority'] ?? 'normal';

    String channelId = notificationType;
    if (priority == 'urgent') {
      channelId = 'urgent';
    }

    final androidDetails = AndroidNotificationDetails(
      channelId,
      channelId.replaceAll('_', ' ').toUpperCase(),
      channelDescription: 'Notifications for $channelId',
      importance: priority == 'urgent' || priority == 'high'
          ? Importance.high
          : Importance.defaultImportance,
      priority: priority == 'urgent'
          ? Priority.max
          : priority == 'high'
              ? Priority.high
              : Priority.defaultPriority,
      icon: android?.smallIcon ?? '@mipmap/ic_launcher',
      playSound: true,
      enableVibration: true,
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    final details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      message.hashCode,
      notification.title,
      notification.body,
      details,
      payload: message.data['notification_id']?.toString(),
    );
  }

  /// Handle notification tap when app is opened from notification
  void _handleMessageTap(RemoteMessage message) {
    debugPrint('Notification tapped: ${message.messageId}');

    // Deep link handling will be done by NotificationHandler
    _messageStreamController.add(message);
  }

  /// Handle local notification tap
  void _handleLocalNotificationTap(NotificationResponse response) {
    debugPrint('Local notification tapped: ${response.payload}');

    // Payload contains notification_id for deep linking
    if (response.payload != null) {
      // Deep link handling will be done by NotificationHandler
    }
  }

  /// Update FCM token on backend
  Future<bool> updateTokenOnBackend(ApiService apiService) async {
    if (_currentToken == null) {
      debugPrint('No FCM token available to update');
      return false;
    }

    try {
      final response = await apiService.put(
        '/notifications/fcm-token',
        data: {'fcm_token': _currentToken},
      );

      if (response.success) {
        debugPrint('FCM token updated on backend successfully');
        return true;
      } else {
        debugPrint('Failed to update FCM token: ${response.message}');
        return false;
      }
    } catch (e) {
      debugPrint('Error updating FCM token: $e');
      return false;
    }
  }

  /// Subscribe to topic
  Future<void> subscribeToTopic(String topic) async {
    try {
      await _messaging.subscribeToTopic(topic);
      debugPrint('Subscribed to topic: $topic');
    } catch (e) {
      debugPrint('Failed to subscribe to topic $topic: $e');
    }
  }

  /// Unsubscribe from topic
  Future<void> unsubscribeFromTopic(String topic) async {
    try {
      await _messaging.unsubscribeFromTopic(topic);
      debugPrint('Unsubscribed from topic: $topic');
    } catch (e) {
      debugPrint('Failed to unsubscribe from topic $topic: $e');
    }
  }

  /// Get badge count (iOS only)
  Future<int?> getBadgeCount() async {
    if (Platform.isIOS) {
      // iOS badge count is managed by the system
      return null;
    }
    return null;
  }

  /// Set badge count (iOS only)
  Future<void> setBadgeCount(int count) async {
    if (Platform.isIOS) {
      // Badge count is set via notification payload on iOS
      debugPrint('Setting badge count: $count');
    }
  }

  /// Clear all notifications
  Future<void> clearAllNotifications() async {
    await _localNotifications.cancelAll();
    debugPrint('All notifications cleared');
  }

  /// Dispose resources
  void dispose() {
    _messageStreamController.close();
    _tokenStreamController.close();
  }
}
