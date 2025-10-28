/// Message provider for bulk SMS/WhatsApp messaging functionality.
///
/// Implements T169 from tasks.md.
library;

import 'package:flutter/foundation.dart';

import '../models/message.dart';
import '../services/api_service.dart';

class MessageProvider with ChangeNotifier {
  MessageProvider(this._apiService);
  final ApiService _apiService;

  List<Message> _messages = [];
  MessageStatistics? _statistics;
  bool _isLoading = false;
  String? _error;

  List<Message> get messages => _messages;
  MessageStatistics? get statistics => _statistics;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Send bulk messages to multiple tenants
  Future<Map<String, dynamic>> sendBulkMessages({
    required List<int> tenantIds,
    required MessageTemplate template,
    required MessageChannel channel,
    String? content,
    DateTime? scheduledAt,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.post(
        '/messages/bulk',
        data: {
          'tenant_ids': tenantIds,
          'template': _templateToString(template),
          'channel': _channelToString(channel),
          'content': content,
          'scheduled_at': scheduledAt?.toIso8601String(),
        },
      );

      if (response.success && response.statusCode == 201) {
        final data = response.data as Map<String, dynamic>;

        // Add messages to local list
        final messagesList = data['messages'] as List;
        _messages.insertAll(
          0,
          messagesList.map((json) => Message.fromJson(json)).toList(),
        );

        _isLoading = false;
        notifyListeners();

        return {
          'success': true,
          'bulk_message_id': data['bulk_message_id'],
          'total_messages': data['total_messages'],
          'successful': data['successful'],
          'failed': data['failed'],
        };
      } else {
        _error = response.message ?? 'Failed to send messages';
        _isLoading = false;
        notifyListeners();

        return {
          'success': false,
          'error': _error,
        };
      }
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      _isLoading = false;
      notifyListeners();

      return {
        'success': false,
        'error': _error,
      };
    }
  }

  /// Schedule messages for future delivery
  Future<Map<String, dynamic>> scheduleMessages({
    required List<int> tenantIds,
    required MessageTemplate template,
    required MessageChannel channel,
    required DateTime scheduledAt,
    String? content,
  }) async =>
      sendBulkMessages(
        tenantIds: tenantIds,
        template: template,
        channel: channel,
        content: content,
        scheduledAt: scheduledAt,
      );

  /// Get message history with filters
  Future<void> fetchMessages({
    int? tenantId,
    MessageChannel? channel,
    MessageStatus? status,
    String? bulkMessageId,
    int limit = 50,
    int offset = 0,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final queryParams = <String, dynamic>{
        'limit': limit,
        'offset': offset,
      };

      if (tenantId != null) {
        queryParams['tenant_id'] = tenantId;
      }
      if (channel != null) {
        queryParams['channel'] = _channelToString(channel);
      }
      if (status != null) {
        queryParams['status'] = _statusToString(status);
      }
      if (bulkMessageId != null) {
        queryParams['bulk_message_id'] = bulkMessageId;
      }

      final response = await _apiService.get(
        '/messages',
        queryParameters: queryParams,
      );

      if (response.success) {
        final data = response.data as List;
        _messages = data.map((json) => Message.fromJson(json)).toList();
        _isLoading = false;
        _error = null;
        notifyListeners();
      } else {
        _error = response.message ?? 'Failed to fetch messages';
        _isLoading = false;
        notifyListeners();
      }
    } catch (e) {
      _error = 'Network error: ${e.toString()}';
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Get message statistics
  Future<void> fetchStatistics({
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    try {
      final queryParams = <String, dynamic>{};

      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String();
      }
      if (endDate != null) {
        queryParams['end_date'] = endDate.toIso8601String();
      }

      final response = await _apiService.get(
        '/messages/statistics',
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      if (response.success) {
        final data = response.data as Map<String, dynamic>;
        _statistics = MessageStatistics.fromJson(data);
        notifyListeners();
      }
    } catch (e) {
      // Silently fail statistics fetch
      debugPrint('Failed to fetch message statistics: $e');
    }
  }

  /// Get a single message by ID
  Future<Message?> getMessage(int messageId) async {
    try {
      final response = await _apiService.get('/messages/$messageId');

      if (response.success) {
        final data = response.data as Map<String, dynamic>;
        return Message.fromJson(data);
      }
      return null;
    } catch (e) {
      debugPrint('Failed to fetch message: $e');
      return null;
    }
  }

  /// Refresh messages (pull-to-refresh)
  Future<void> refreshMessages() async {
    await fetchMessages();
    await fetchStatistics();
  }

  /// Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }

  // Helper methods for enum conversion
  String _channelToString(MessageChannel channel) {
    switch (channel) {
      case MessageChannel.sms:
        return 'sms';
      case MessageChannel.whatsapp:
        return 'whatsapp';
      case MessageChannel.email:
        return 'email';
    }
  }

  String _statusToString(MessageStatus status) {
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

  String _templateToString(MessageTemplate template) {
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
