/// Notification provider for managing push notifications.
///
/// Implements T246 from tasks.md.
library;

import 'package:flutter/foundation.dart';

import '../models/notification.dart';
import '../services/api_service.dart';
import '../services/fcm_service.dart';

class NotificationProvider with ChangeNotifier {
  NotificationProvider(this._apiService, this._fcmService) {
    _initialize();
  }
  final ApiService _apiService;
  final FCMService _fcmService;

  List<AppNotification> _notifications = [];
  int _unreadCount = 0;
  Map<String, int> _unreadByType = {};
  Map<String, int> _unreadByPriority = {};
  bool _isLoading = false;
  String? _error;

  List<AppNotification> get notifications => _notifications;
  List<AppNotification> get unreadNotifications =>
      _notifications.where((n) => !n.isRead).toList();
  int get unreadCount => _unreadCount;
  Map<String, int> get unreadByType => _unreadByType;
  Map<String, int> get unreadByPriority => _unreadByPriority;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Initialize notification provider
  void _initialize() {
    // Listen to FCM messages
    _fcmService.messageStream.listen((message) {
      // Refresh notifications when a new one arrives
      fetchNotifications();
    });

    // Listen to FCM token updates
    _fcmService.tokenStream.listen(_updateFCMToken);
  }

  /// Update FCM token on backend
  Future<void> _updateFCMToken(String token) async {
    try {
      await _fcmService.updateTokenOnBackend(_apiService);
    } catch (e) {
      debugPrint('Failed to update FCM token: $e');
    }
  }

  /// Fetch notifications with optional filters
  Future<void> fetchNotifications({
    NotificationType? type,
    NotificationPriority? priority,
    bool? isRead,
    int page = 1,
    int pageSize = 20,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'page_size': pageSize,
      };

      if (type != null) {
        queryParams['notification_type'] = type.value;
      }
      if (priority != null) {
        queryParams['priority'] = priority.value;
      }
      if (isRead != null) {
        queryParams['is_read'] = isRead;
      }

      final response = await _apiService.get(
        '/notifications',
        queryParameters: queryParams,
      );

      _isLoading = false;

      if (response.success) {
        final listResponse = NotificationListResponse.fromJson(
          response.data as Map<String, dynamic>,
        );
        _notifications = listResponse.notifications;
        notifyListeners();
      } else {
        _error = response.message ?? 'Failed to fetch notifications';
        notifyListeners();
      }
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Fetch unread notification count
  Future<void> fetchUnreadCount() async {
    try {
      final response = await _apiService.get('/notifications/unread-count');

      if (response.success) {
        final countResponse = UnreadCountResponse.fromJson(
          response.data as Map<String, dynamic>,
        );
        _unreadCount = countResponse.unreadCount;
        _unreadByType = countResponse.byType;
        _unreadByPriority = countResponse.byPriority;
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Failed to fetch unread count: $e');
    }
  }

  /// Mark notifications as read
  Future<bool> markAsRead(List<int> notificationIds) async {
    try {
      final response = await _apiService.patch(
        '/notifications/mark-read',
        data: {'notification_ids': notificationIds},
      );

      if (response.success) {
        // Update local state
        for (final id in notificationIds) {
          final index = _notifications.indexWhere((n) => n.id == id);
          if (index != -1) {
            _notifications[index] = _notifications[index].copyWith(
              isRead: true,
              readAt: DateTime.now(),
            );
          }
        }

        // Update unread count
        _unreadCount = _notifications.where((n) => !n.isRead).length;
        notifyListeners();

        return true;
      } else {
        _error = response.message ?? 'Failed to mark as read';
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      notifyListeners();
      return false;
    }
  }

  /// Mark all notifications as read
  Future<bool> markAllAsRead() async {
    final unreadIds =
        _notifications.where((n) => !n.isRead).map((n) => n.id).toList();

    if (unreadIds.isEmpty) {
      return true;
    }

    return markAsRead(unreadIds);
  }

  /// Get notifications grouped by type
  Map<NotificationType, List<AppNotification>> getGroupedByType() {
    final grouped = <NotificationType, List<AppNotification>>{};

    for (final notification in _notifications) {
      grouped
          .putIfAbsent(
            notification.notificationType,
            () => [],
          )
          .add(notification);
    }

    return grouped;
  }

  /// Get notifications grouped by date
  Map<String, List<AppNotification>> getGroupedByDate() {
    final grouped = <String, List<AppNotification>>{};

    for (final notification in _notifications) {
      final dateKey = _getDateKey(notification.createdAt);
      grouped.putIfAbsent(dateKey, () => []).add(notification);
    }

    return grouped;
  }

  /// Get date key for grouping
  String _getDateKey(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final notificationDate = DateTime(date.year, date.month, date.day);

    if (notificationDate == today) {
      return 'Today';
    } else if (notificationDate == yesterday) {
      return 'Yesterday';
    } else if (now.difference(notificationDate).inDays < 7) {
      return 'This Week';
    } else if (now.difference(notificationDate).inDays < 30) {
      return 'This Month';
    } else {
      return 'Earlier';
    }
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }

  /// Refresh notifications
  Future<void> refresh() async {
    await Future.wait([
      fetchNotifications(),
      fetchUnreadCount(),
    ]);
  }
}
