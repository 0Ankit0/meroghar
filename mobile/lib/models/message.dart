/// Message model for SMS/WhatsApp/Email communications.
///
/// Implements T168 from tasks.md.
library;

enum MessageChannel {
  sms,
  whatsapp,
  email,
}

enum MessageStatus {
  pending,
  scheduled,
  sending,
  sent,
  delivered,
  failed,
  cancelled,
}

enum MessageTemplate {
  paymentReminder,
  paymentOverdue,
  paymentReceived,
  leaseExpiring,
  maintenanceNotice,
  custom,
}

class Message {
  final int id;
  final int tenantId;
  final int? sentBy;
  final int? propertyId;
  final MessageTemplate template;
  final String? subject;
  final String content;
  final MessageChannel channel;
  final String? recipientPhone;
  final String? recipientEmail;
  final MessageStatus status;
  final DateTime? scheduledAt;
  final DateTime? sentAt;
  final DateTime? deliveredAt;
  final String? errorMessage;
  final int retryCount;
  final String? providerMessageId;
  final Map<String, dynamic>? providerResponse;
  final String? bulkMessageId;
  final Map<String, dynamic>? metadata;
  final DateTime createdAt;
  final DateTime? updatedAt;

  // Computed properties
  bool get isPending => status == MessageStatus.pending;
  bool get isScheduled => status == MessageStatus.scheduled;
  bool get isSent => status == MessageStatus.sent;
  bool get isDelivered => status == MessageStatus.delivered;
  bool get hasFailed => status == MessageStatus.failed;
  bool get canRetry => hasFailed && retryCount < 3;

  Message({
    required this.id,
    required this.tenantId,
    this.sentBy,
    this.propertyId,
    required this.template,
    this.subject,
    required this.content,
    required this.channel,
    this.recipientPhone,
    this.recipientEmail,
    required this.status,
    this.scheduledAt,
    this.sentAt,
    this.deliveredAt,
    this.errorMessage,
    required this.retryCount,
    this.providerMessageId,
    this.providerResponse,
    this.bulkMessageId,
    this.metadata,
    required this.createdAt,
    this.updatedAt,
  });

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] as int,
      tenantId: json['tenant_id'] as int,
      sentBy: json['sent_by'] as int?,
      propertyId: json['property_id'] as int?,
      template: _templateFromString(json['template'] as String),
      subject: json['subject'] as String?,
      content: json['content'] as String,
      channel: _channelFromString(json['channel'] as String),
      recipientPhone: json['recipient_phone'] as String?,
      recipientEmail: json['recipient_email'] as String?,
      status: _statusFromString(json['status'] as String),
      scheduledAt: json['scheduled_at'] != null
          ? DateTime.parse(json['scheduled_at'] as String)
          : null,
      sentAt: json['sent_at'] != null
          ? DateTime.parse(json['sent_at'] as String)
          : null,
      deliveredAt: json['delivered_at'] != null
          ? DateTime.parse(json['delivered_at'] as String)
          : null,
      errorMessage: json['error_message'] as String?,
      retryCount: json['retry_count'] as int? ?? 0,
      providerMessageId: json['provider_message_id'] as String?,
      providerResponse: json['provider_response'] as Map<String, dynamic>?,
      bulkMessageId: json['bulk_message_id'] as String?,
      metadata: json['metadata'] as Map<String, dynamic>?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'tenant_id': tenantId,
      'sent_by': sentBy,
      'property_id': propertyId,
      'template': _templateToString(template),
      'subject': subject,
      'content': content,
      'channel': _channelToString(channel),
      'recipient_phone': recipientPhone,
      'recipient_email': recipientEmail,
      'status': _statusToString(status),
      'scheduled_at': scheduledAt?.toIso8601String(),
      'sent_at': sentAt?.toIso8601String(),
      'delivered_at': deliveredAt?.toIso8601String(),
      'error_message': errorMessage,
      'retry_count': retryCount,
      'provider_message_id': providerMessageId,
      'provider_response': providerResponse,
      'bulk_message_id': bulkMessageId,
      'metadata': metadata,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt?.toIso8601String(),
    };
  }

  Message copyWith({
    int? id,
    int? tenantId,
    int? sentBy,
    int? propertyId,
    MessageTemplate? template,
    String? subject,
    String? content,
    MessageChannel? channel,
    String? recipientPhone,
    String? recipientEmail,
    MessageStatus? status,
    DateTime? scheduledAt,
    DateTime? sentAt,
    DateTime? deliveredAt,
    String? errorMessage,
    int? retryCount,
    String? providerMessageId,
    Map<String, dynamic>? providerResponse,
    String? bulkMessageId,
    Map<String, dynamic>? metadata,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return Message(
      id: id ?? this.id,
      tenantId: tenantId ?? this.tenantId,
      sentBy: sentBy ?? this.sentBy,
      propertyId: propertyId ?? this.propertyId,
      template: template ?? this.template,
      subject: subject ?? this.subject,
      content: content ?? this.content,
      channel: channel ?? this.channel,
      recipientPhone: recipientPhone ?? this.recipientPhone,
      recipientEmail: recipientEmail ?? this.recipientEmail,
      status: status ?? this.status,
      scheduledAt: scheduledAt ?? this.scheduledAt,
      sentAt: sentAt ?? this.sentAt,
      deliveredAt: deliveredAt ?? this.deliveredAt,
      errorMessage: errorMessage ?? this.errorMessage,
      retryCount: retryCount ?? this.retryCount,
      providerMessageId: providerMessageId ?? this.providerMessageId,
      providerResponse: providerResponse ?? this.providerResponse,
      bulkMessageId: bulkMessageId ?? this.bulkMessageId,
      metadata: metadata ?? this.metadata,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
    );
  }

  // Helper methods for enum conversion
  static MessageChannel _channelFromString(String value) {
    switch (value) {
      case 'sms':
        return MessageChannel.sms;
      case 'whatsapp':
        return MessageChannel.whatsapp;
      case 'email':
        return MessageChannel.email;
      default:
        throw ArgumentError('Invalid channel: $value');
    }
  }

  static String _channelToString(MessageChannel channel) {
    switch (channel) {
      case MessageChannel.sms:
        return 'sms';
      case MessageChannel.whatsapp:
        return 'whatsapp';
      case MessageChannel.email:
        return 'email';
    }
  }

  static MessageStatus _statusFromString(String value) {
    switch (value) {
      case 'pending':
        return MessageStatus.pending;
      case 'scheduled':
        return MessageStatus.scheduled;
      case 'sending':
        return MessageStatus.sending;
      case 'sent':
        return MessageStatus.sent;
      case 'delivered':
        return MessageStatus.delivered;
      case 'failed':
        return MessageStatus.failed;
      case 'cancelled':
        return MessageStatus.cancelled;
      default:
        throw ArgumentError('Invalid status: $value');
    }
  }

  static String _statusToString(MessageStatus status) {
    switch (status) {
      case MessageStatus.pending:
        return 'pending';
      case MessageStatus.scheduled:
        return 'scheduled';
      case MessageStatus.sending:
        return 'sending';
      case MessageStatus.sent:
        return 'sent';
      case MessageStatus.delivered:
        return 'delivered';
      case MessageStatus.failed:
        return 'failed';
      case MessageStatus.cancelled:
        return 'cancelled';
    }
  }

  static MessageTemplate _templateFromString(String value) {
    switch (value) {
      case 'payment_reminder':
        return MessageTemplate.paymentReminder;
      case 'payment_overdue':
        return MessageTemplate.paymentOverdue;
      case 'payment_received':
        return MessageTemplate.paymentReceived;
      case 'lease_expiring':
        return MessageTemplate.leaseExpiring;
      case 'maintenance_notice':
        return MessageTemplate.maintenanceNotice;
      case 'custom':
        return MessageTemplate.custom;
      default:
        throw ArgumentError('Invalid template: $value');
    }
  }

  static String _templateToString(MessageTemplate template) {
    switch (template) {
      case MessageTemplate.paymentReminder:
        return 'payment_reminder';
      case MessageTemplate.paymentOverdue:
        return 'payment_overdue';
      case MessageTemplate.paymentReceived:
        return 'payment_received';
      case MessageTemplate.leaseExpiring:
        return 'lease_expiring';
      case MessageTemplate.maintenanceNotice:
        return 'maintenance_notice';
      case MessageTemplate.custom:
        return 'custom';
    }
  }
}

/// Statistics for message delivery
class MessageStatistics {
  final int totalMessages;
  final int sent;
  final int delivered;
  final int failed;
  final int pending;
  final double deliveryRate;

  MessageStatistics({
    required this.totalMessages,
    required this.sent,
    required this.delivered,
    required this.failed,
    required this.pending,
    required this.deliveryRate,
  });

  factory MessageStatistics.fromJson(Map<String, dynamic> json) {
    return MessageStatistics(
      totalMessages: json['total_messages'] as int,
      sent: json['sent'] as int,
      delivered: json['delivered'] as int,
      failed: json['failed'] as int,
      pending: json['pending'] as int,
      deliveryRate: (json['delivery_rate'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total_messages': totalMessages,
      'sent': sent,
      'delivered': delivered,
      'failed': failed,
      'pending': pending,
      'delivery_rate': deliveryRate,
    };
  }
}
