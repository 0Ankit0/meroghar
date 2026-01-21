/// Maintenance Request model.
library;

import 'package:intl/intl.dart';

enum MaintenanceStatus {
  open('open', 'Open'),
  inProgress('in_progress', 'In Progress'),
  resolved('resolved', 'Resolved'),
  closed('closed', 'Closed');

  const MaintenanceStatus(this.value, this.label);
  final String value;
  final String label;

  static MaintenanceStatus fromValue(String value) {
    return MaintenanceStatus.values.firstWhere(
      (e) => e.value == value,
      orElse: () => MaintenanceStatus.open,
    );
  }
}

enum MaintenancePriority {
  low('low', 'Low'),
  medium('medium', 'Medium'),
  high('high', 'High'),
  urgent('urgent', 'Urgent');

  const MaintenancePriority(this.value, this.label);
  final String value;
  final String label;

  static MaintenancePriority fromValue(String value) {
    return MaintenancePriority.values.firstWhere(
      (e) => e.value == value,
      orElse: () => MaintenancePriority.medium,
    );
  }
}

class MaintenanceRequest {
  MaintenanceRequest({
    required this.id,
    required this.title,
    required this.description,
    required this.status,
    required this.priority,
    required this.propertyId,
    required this.createdAt,
    this.propertyName,
    this.requestedBy,
    this.requesterName,
    this.assignedTo,
    this.assigneeName,
    this.resolutionNotes,
    this.scheduledDate,
    this.resolvedAt,
    this.images = const [],
  });

  factory MaintenanceRequest.fromJson(Map<String, dynamic> json) {
    return MaintenanceRequest(
      id: json['id'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      status: MaintenanceStatus.fromValue(json['status'] as String),
      priority: MaintenancePriority.fromValue(json['priority'] as String),
      propertyId: json['property_id'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      propertyName: json['property_name'] as String?,
      requestedBy: json['requested_by'] as String?,
      requesterName: json['requester_name'] as String?,
      assignedTo: json['assigned_to'] as String?,
      assigneeName: json['assignee_name'] as String?,
      resolutionNotes: json['resolution_notes'] as String?,
      scheduledDate: json['scheduled_date'] != null
          ? DateTime.parse(json['scheduled_date'] as String)
          : null,
      resolvedAt: json['resolved_at'] != null
          ? DateTime.parse(json['resolved_at'] as String)
          : null,
      images: (json['images'] as List<dynamic>?)?.cast<String>() ?? [],
    );
  }

  final String id;
  final String title;
  final String description;
  final MaintenanceStatus status;
  final MaintenancePriority priority;
  final String propertyId;
  final DateTime createdAt;
  final String? propertyName;
  final String? requestedBy;
  final String? requesterName;
  final String? assignedTo;
  final String? assigneeName;
  final String? resolutionNotes;
  final DateTime? scheduledDate;
  final DateTime? resolvedAt;
  final List<String> images;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'status': status.value,
      'priority': priority.value,
      'property_id': propertyId,
      'created_at': createdAt.toIso8601String(),
      'property_name': propertyName,
    };
  }
}
