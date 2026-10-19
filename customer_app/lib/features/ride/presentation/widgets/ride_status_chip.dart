import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../models/ride.dart';

class RideStatusChip extends StatelessWidget {
  const RideStatusChip({super.key, required this.status});

  final RideStatus status;

  @override
  Widget build(BuildContext context) {
    final (label, background, foreground) = switch (status) {
      RideStatus.completed => ('Completed', AppColors.success.withValues(alpha: 0.12), AppColors.success),
      RideStatus.cancelled => ('Cancelled', AppColors.danger.withValues(alpha: 0.1), AppColors.danger),
      RideStatus.requested || RideStatus.searching => ('Searching', AppColors.brand, AppColors.ink),
      RideStatus.unknown => ('Unknown', AppColors.surface, AppColors.textSecondary),
      _ => ('On trip', AppColors.ink, AppColors.onInk),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: background, borderRadius: BorderRadius.circular(999)),
      child: Text(
        label,
        style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: foreground),
      ),
    );
  }
}
