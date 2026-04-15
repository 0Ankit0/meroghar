import 'package:flutter/material.dart';
import '../data/models/booking.dart';

extension BookingStatusPresentation on String {
  String get bookingStatusLabel {
    switch (normalizeBookingStatus(this)) {
      case 'PENDING':
        return 'Pending';
      case 'CONFIRMED':
        return 'Confirmed';
      case 'ACTIVE':
        return 'Active';
      case 'PENDING_CLOSURE':
        return 'Pending closure';
      case 'CLOSED':
        return 'Closed';
      case 'CANCELLED':
        return 'Cancelled';
      case 'DECLINED':
        return 'Declined';
      default:
        return normalizeBookingStatus(this)
            .toLowerCase()
            .split('_')
            .map((part) => part.isEmpty
                ? part
                : '${part[0].toUpperCase()}${part.substring(1)}')
            .join(' ');
    }
  }

  IconData get bookingStatusIcon {
    switch (normalizeBookingStatus(this)) {
      case 'PENDING':
        return Icons.schedule_outlined;
      case 'CONFIRMED':
        return Icons.check_circle_outline;
      case 'ACTIVE':
        return Icons.home_work_outlined;
      case 'PENDING_CLOSURE':
        return Icons.assignment_turned_in_outlined;
      case 'CLOSED':
        return Icons.task_alt_outlined;
      case 'CANCELLED':
        return Icons.cancel_outlined;
      case 'DECLINED':
        return Icons.block_outlined;
      default:
        return Icons.info_outline;
    }
  }

  Color bookingStatusColor(ColorScheme colorScheme) {
    switch (normalizeBookingStatus(this)) {
      case 'PENDING':
        return Colors.orange;
      case 'CONFIRMED':
        return Colors.blue;
      case 'ACTIVE':
        return Colors.green;
      case 'PENDING_CLOSURE':
        return Colors.deepPurple;
      case 'CLOSED':
        return Colors.teal;
      case 'CANCELLED':
      case 'DECLINED':
        return colorScheme.error;
      default:
        return colorScheme.primary;
    }
  }
}
