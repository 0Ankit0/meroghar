import 'package:flutter/material.dart';

extension AgreementStatusPresentation on String {
  String get agreementStatusLabel {
    switch (this) {
      case 'DRAFT':
        return 'Draft';
      case 'PENDING_CUSTOMER_SIGNATURE':
        return 'Waiting for tenant';
      case 'PENDING_OWNER_SIGNATURE':
        return 'Waiting for landlord';
      case 'SIGNED':
        return 'Signed';
      case 'AMENDED':
        return 'Amended';
      case 'TERMINATED':
        return 'Terminated';
      default:
        return toLowerCase()
            .split('_')
            .map((part) => part.isEmpty
                ? part
                : '${part[0].toUpperCase()}${part.substring(1)}')
            .join(' ');
    }
  }

  IconData get agreementStatusIcon {
    switch (this) {
      case 'DRAFT':
        return Icons.description_outlined;
      case 'PENDING_CUSTOMER_SIGNATURE':
        return Icons.edit_note_outlined;
      case 'PENDING_OWNER_SIGNATURE':
        return Icons.approval_outlined;
      case 'SIGNED':
        return Icons.verified_outlined;
      case 'AMENDED':
        return Icons.history_toggle_off_outlined;
      case 'TERMINATED':
        return Icons.gpp_bad_outlined;
      default:
        return Icons.article_outlined;
    }
  }

  Color agreementStatusColor(ColorScheme colorScheme) {
    switch (this) {
      case 'DRAFT':
        return Colors.grey;
      case 'PENDING_CUSTOMER_SIGNATURE':
        return Colors.orange;
      case 'PENDING_OWNER_SIGNATURE':
        return Colors.blue;
      case 'SIGNED':
        return Colors.green;
      case 'AMENDED':
        return Colors.deepPurple;
      case 'TERMINATED':
        return colorScheme.error;
      default:
        return colorScheme.primary;
    }
  }
}
