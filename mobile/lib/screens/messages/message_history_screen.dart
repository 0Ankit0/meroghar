/// Message history screen with delivery tracking.
///
/// Implements T172 from tasks.md.
library;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../models/message.dart';
import '../../providers/message_provider.dart';
import '../../widgets/message_status_widget.dart';

class MessageHistoryScreen extends StatefulWidget {
  const MessageHistoryScreen({super.key});

  @override
  State<MessageHistoryScreen> createState() => _MessageHistoryScreenState();
}

class _MessageHistoryScreenState extends State<MessageHistoryScreen> {
  MessageChannel? _channelFilter;
  MessageStatus? _statusFilter;

  @override
  void initState() {
    super.initState();
    // Load messages on init
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadMessages();
    });
  }

  Future<void> _loadMessages() async {
    await context.read<MessageProvider>().fetchMessages(
          channel: _channelFilter,
          status: _statusFilter,
        );
  }

  Future<void> _refreshMessages() async {
    await context.read<MessageProvider>().refreshMessages();
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Filter Messages'),
        content: StatefulBuilder(
          builder: (context, setState) => Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Channel filter
              const Text(
                'Channel',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<MessageChannel?>(
                value: _channelFilter,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'All Channels',
                ),
                items: [
                  const DropdownMenuItem(
                    child: Text('All Channels'),
                  ),
                  ...MessageChannel.values.map(
                    (channel) => DropdownMenuItem(
                      value: channel,
                      child: Text(_getChannelName(channel)),
                    ),
                  ),
                ],
                onChanged: (value) {
                  setState(() {
                    _channelFilter = value;
                  });
                },
              ),
              const SizedBox(height: 16),

              // Status filter
              const Text(
                'Status',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<MessageStatus?>(
                value: _statusFilter,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'All Statuses',
                ),
                items: [
                  const DropdownMenuItem(
                    child: Text('All Statuses'),
                  ),
                  ...MessageStatus.values.map(
                    (status) => DropdownMenuItem(
                      value: status,
                      child: Text(_getStatusName(status)),
                    ),
                  ),
                ],
                onChanged: (value) {
                  setState(() {
                    _statusFilter = value;
                  });
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              setState(() {
                _channelFilter = null;
                _statusFilter = null;
              });
              Navigator.pop(context);
              _loadMessages();
            },
            child: const Text('Clear'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _loadMessages();
            },
            child: const Text('Apply'),
          ),
        ],
      ),
    );
  }

  String _getChannelName(MessageChannel channel) {
    switch (channel) {
      case MessageChannel.sms:
        return 'SMS';
      case MessageChannel.whatsapp:
        return 'WhatsApp';
      case MessageChannel.email:
        return 'Email';
    }
  }

  String _getStatusName(MessageStatus status) {
    switch (status) {
      case MessageStatus.pending:
        return 'Pending';
      case MessageStatus.scheduled:
        return 'Scheduled';
      case MessageStatus.sending:
        return 'Sending';
      case MessageStatus.sent:
        return 'Sent';
      case MessageStatus.delivered:
        return 'Delivered';
      case MessageStatus.failed:
        return 'Failed';
      case MessageStatus.cancelled:
        return 'Cancelled';
    }
  }

  String _formatDateTime(DateTime dt) =>
      '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
          title: const Text('Message History'),
          actions: [
            IconButton(
              icon: const Icon(Icons.filter_list),
              onPressed: _showFilterDialog,
            ),
          ],
        ),
        body: Consumer<MessageProvider>(
          builder: (context, messageProvider, child) {
            if (messageProvider.isLoading && messageProvider.messages.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }

            if (messageProvider.error != null &&
                messageProvider.messages.isEmpty) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      messageProvider.error!,
                      style: const TextStyle(color: Colors.red),
                    ),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: _loadMessages,
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              );
            }

            if (messageProvider.messages.isEmpty) {
              return const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.message_outlined,
                      size: 64,
                      color: Colors.grey,
                    ),
                    SizedBox(height: 16),
                    Text(
                      'No messages found',
                      style: TextStyle(fontSize: 16, color: Colors.grey),
                    ),
                    SizedBox(height: 8),
                    Text(
                      'Send your first bulk message',
                      style: TextStyle(fontSize: 14, color: Colors.grey),
                    ),
                  ],
                ),
              );
            }

            return Column(
              children: [
                // Statistics Card
                if (messageProvider.statistics != null)
                  Card(
                    margin: const EdgeInsets.all(16),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Statistics',
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 12),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceAround,
                            children: [
                              _buildStatItem(
                                'Total',
                                messageProvider.statistics!.totalMessages
                                    .toString(),
                                Colors.blue,
                              ),
                              _buildStatItem(
                                'Sent',
                                messageProvider.statistics!.sent.toString(),
                                Colors.orange,
                              ),
                              _buildStatItem(
                                'Delivered',
                                messageProvider.statistics!.delivered
                                    .toString(),
                                Colors.green,
                              ),
                              _buildStatItem(
                                'Failed',
                                messageProvider.statistics!.failed.toString(),
                                Colors.red,
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          LinearProgressIndicator(
                            value:
                                messageProvider.statistics!.deliveryRate / 100,
                            backgroundColor: Colors.grey[300],
                            color: Colors.green,
                          ),
                          const SizedBox(height: 8),
                          Center(
                            child: Text(
                              'Delivery Rate: ${messageProvider.statistics!.deliveryRate.toStringAsFixed(1)}%',
                              style: const TextStyle(fontSize: 14),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                // Messages List
                Expanded(
                  child: RefreshIndicator(
                    onRefresh: _refreshMessages,
                    child: ListView.builder(
                      itemCount: messageProvider.messages.length,
                      itemBuilder: (context, index) {
                        final message = messageProvider.messages[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 8,
                          ),
                          child: ListTile(
                            leading: MessageStatusWidget(message: message),
                            title: Text(
                              _getTemplateName(message.template),
                              style:
                                  const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 4),
                                Text(
                                  message.content.length > 60
                                      ? '${message.content.substring(0, 60)}...'
                                      : message.content,
                                ),
                                const SizedBox(height: 4),
                                Row(
                                  children: [
                                    Icon(
                                      _getChannelIcon(message.channel),
                                      size: 16,
                                      color: Colors.grey,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      _getChannelName(message.channel),
                                      style: const TextStyle(fontSize: 12),
                                    ),
                                    const SizedBox(width: 16),
                                    const Icon(
                                      Icons.access_time,
                                      size: 16,
                                      color: Colors.grey,
                                    ),
                                    const SizedBox(width: 4),
                                    Text(
                                      _formatDateTime(message.createdAt),
                                      style: const TextStyle(fontSize: 12),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            isThreeLine: true,
                            trailing: message.bulkMessageId != null
                                ? const Icon(Icons.group)
                                : null,
                            onTap: () => _showMessageDetails(message),
                          ),
                        );
                      },
                    ),
                  ),
                ),
              ],
            );
          },
        ),
      );

  Widget _buildStatItem(String label, String value, Color color) => Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],
      );

  String _getTemplateName(MessageTemplate template) {
    switch (template) {
      case MessageTemplate.paymentReminder:
        return 'Payment Reminder';
      case MessageTemplate.paymentOverdue:
        return 'Payment Overdue';
      case MessageTemplate.paymentReceived:
        return 'Payment Received';
      case MessageTemplate.leaseExpiring:
        return 'Lease Expiring';
      case MessageTemplate.maintenanceNotice:
        return 'Maintenance Notice';
      case MessageTemplate.custom:
        return 'Custom Message';
    }
  }

  IconData _getChannelIcon(MessageChannel channel) {
    switch (channel) {
      case MessageChannel.sms:
        return Icons.sms;
      case MessageChannel.whatsapp:
        return Icons.chat;
      case MessageChannel.email:
        return Icons.email;
    }
  }

  void _showMessageDetails(Message message) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  MessageStatusWidget(message: message),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _getTemplateName(message.template),
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(
                          _getChannelName(message.channel),
                          style: const TextStyle(color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Text(
                'Message Content',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(message.content),
              const SizedBox(height: 24),
              const Text(
                'Details',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              _buildDetailRow('Created', _formatDateTime(message.createdAt)),
              if (message.scheduledAt != null)
                _buildDetailRow(
                    'Scheduled', _formatDateTime(message.scheduledAt!)),
              if (message.sentAt != null)
                _buildDetailRow('Sent', _formatDateTime(message.sentAt!)),
              if (message.deliveredAt != null)
                _buildDetailRow(
                    'Delivered', _formatDateTime(message.deliveredAt!)),
              if (message.recipientPhone != null)
                _buildDetailRow('Phone', message.recipientPhone!),
              if (message.recipientEmail != null)
                _buildDetailRow('Email', message.recipientEmail!),
              if (message.bulkMessageId != null)
                _buildDetailRow('Bulk ID', message.bulkMessageId!),
              if (message.errorMessage != null) ...[
                const SizedBox(height: 16),
                const Text(
                  'Error',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.red,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  message.errorMessage!,
                  style: const TextStyle(color: Colors.red),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SizedBox(
              width: 100,
              child: Text(
                label,
                style: const TextStyle(color: Colors.grey),
              ),
            ),
            Expanded(
              child: Text(value),
            ),
          ],
        ),
      );
}
