/// Notification model for push notifications.
///
/// Implements T246 from tasks.md.
library;

/// Notification type enumeration
enum NotificationType {
  paymentReceived('payment_received'),
  paymentOverdue('payment_overdue'),
  billCreated('bill_created'),
  billAllocated('bill_allocated'),
  documentUploaded('document_uploaded'),
  documentExpiring('document_expiring'),
  rentIncrement('rent_increment'),
  messageReceived('message_received'),
  expenseSubmitted('expense_submitted'),
  expenseApproved('expense_approved'),
  leaseExpiring('lease_expiring'),
  maintenanceScheduled('maintenance_scheduled'),
  systemAnnouncement('system_announcement');

  const NotificationType(this.value);
  final String value;

  static NotificationType fromString(String value) =>
      NotificationType.values.firstWhere(
        (e) => e.value == value,
        orElse: () => NotificationType.systemAnnouncement,
      );

  String get displayName {
    switch (this) {
      case NotificationType.paymentReceived:
        return 'Payment Received';
      case NotificationType.paymentOverdue:
        return 'Payment Overdue';
      case NotificationType.billCreated:
        return 'New Bill';
      case NotificationType.billAllocated:
        return 'Bill Allocated';
      case NotificationType.documentUploaded:
        return 'Document Uploaded';
      case NotificationType.documentExpiring:
        return 'Document Expiring';
      case NotificationType.rentIncrement:
        return 'Rent Increment';
      case NotificationType.messageReceived:
        return 'New Message';
      case NotificationType.expenseSubmitted:
        return 'Expense Submitted';
      case NotificationType.expenseApproved:
        return 'Expense Approved';
      case NotificationType.leaseExpiring:
        return 'Lease Expiring';
      case NotificationType.maintenanceScheduled:
        return 'Maintenance Scheduled';
      case NotificationType.systemAnnouncement:
        return 'Announcement';
    }
  }
}

/// Notification priority enumeration
enum NotificationPriority {
  low('low'),
  normal('normal'),
  high('high'),
  urgent('urgent');

  const NotificationPriority(this.value);
  final String value;

  static NotificationPriority fromString(String value) =>
      NotificationPriority.values.firstWhere(
        (e) => e.value == value,
        orElse: () => NotificationPriority.normal,
      );
}

/// Notification model
class AppNotification {
  AppNotification({
    required this.id,
    required this.userId,
    required this.title,
    required this.body,
    required this.notificationType,
    required this.priority,
    this.deepLink,
    this.metadata,
    required this.isRead,
    this.readAt,
    this.fcmMessageId,
    this.sentAt,
    required this.deliveryFailed,
    this.failureReason,
    required this.createdAt,
    this.updatedAt,
  });

  factory AppNotification.fromJson(Map<String, dynamic> json) {
    return AppNotification(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      title: json['title'] as String,
      body: json['body'] as String,
      notificationType:
          NotificationType.fromString(json['notification_type'] as String),
      priority: NotificationPriority.fromString(json['priority'] as String),
      deepLink: json['deep_link'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>?,
      isRead: json['is_read'] as bool,
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at']) : null,
      fcmMessageId: json['fcm_message_id'] as String?,
      sentAt: json['sent_at'] != null ? DateTime.parse(json['sent_at']) : null,
      deliveryFailed: json['delivery_failed'] as bool,
      failureReason: json['failure_reason'] as String?,
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'])
          : null,
    );
  }
  final int id;
  final int userId;
  final String title;
  final String body;
  final NotificationType notificationType;
  final NotificationPriority priority;
  final String? deepLink;
  final Map<String, dynamic>? metadata;
  final bool isRead;
  final DateTime? readAt;
  final String? fcmMessageId;
  final DateTime? sentAt;
  final bool deliveryFailed;
  final String? failureReason;
  final DateTime createdAt;
  final DateTime? updatedAt;

  Map<String, dynamic> toJson() => {
        'id': id,
        'user_id': userId,
        'title': title,
        'body': body,
        'notification_type': notificationType.value,
        'priority': priority.value,
        'deep_link': deepLink,
        'metadata': metadata,
        'is_read': isRead,
        'read_at': readAt?.toIso8601String(),
        'fcm_message_id': fcmMessageId,
        'sent_at': sentAt?.toIso8601String(),
        'delivery_failed': deliveryFailed,
        'failure_reason': failureReason,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt?.toIso8601String(),
      };

  AppNotification copyWith({
    int? id,
    int? userId,
    String? title,
    String? body,
    NotificationType? notificationType,
    NotificationPriority? priority,
    String? deepLink,
    Map<String, dynamic>? metadata,
    bool? isRead,
    DateTime? readAt,
    String? fcmMessageId,
    DateTime? sentAt,
    bool? deliveryFailed,
    String? failureReason,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) =>
      AppNotification(
        id: id ?? this.id,
        userId: userId ?? this.userId,
        title: title ?? this.title,
        body: body ?? this.body,
        notificationType: notificationType ?? this.notificationType,
        priority: priority ?? this.priority,
        deepLink: deepLink ?? this.deepLink,
        metadata: metadata ?? this.metadata,
        isRead: isRead ?? this.isRead,
        readAt: readAt ?? this.readAt,
        fcmMessageId: fcmMessageId ?? this.fcmMessageId,
        sentAt: sentAt ?? this.sentAt,
        deliveryFailed: deliveryFailed ?? this.deliveryFailed,
        failureReason: failureReason ?? this.failureReason,
        createdAt: createdAt ?? this.createdAt,
        updatedAt: updatedAt ?? this.updatedAt,
      );
}

/// Notification list response
class NotificationListResponse {
  NotificationListResponse({
    required this.notifications,
    required this.total,
    required this.page,
    required this.pageSize,
    required this.totalPages,
  });

  factory NotificationListResponse.fromJson(Map<String, dynamic> json) {
    return NotificationListResponse(
      notifications: (json['notifications'] as List)
          .map((e) => AppNotification.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      pageSize: json['page_size'] as int,
      totalPages: json['total_pages'] as int,
    );
  }
  final List<AppNotification> notifications;
  final int total;
  final int page;
  final int pageSize;
  final int totalPages;
}

/// Unread count response
class UnreadCountResponse {
  UnreadCountResponse({
    required this.unreadCount,
    required this.byType,
    required this.byPriority,
  });

  factory UnreadCountResponse.fromJson(Map<String, dynamic> json) {
    return UnreadCountResponse(
      unreadCount: json['unread_count'] as int,
      byType: Map<String, int>.from(json['by_type'] as Map),
      byPriority: Map<String, int>.from(json['by_priority'] as Map),
    );
  }
  final int unreadCount;
  final Map<String, int> byType;
  final Map<String, int> byPriority;
}
