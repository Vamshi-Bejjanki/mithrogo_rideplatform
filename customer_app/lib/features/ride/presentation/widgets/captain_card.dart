import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../models/ride_tracking.dart';

/// Captain name, rating, and vehicle with the plate number, like the "your driver" card in Uber and Rapido.
class CaptainCard extends StatelessWidget {
  const CaptainCard({super.key, required this.captain});

  final CaptainInfo captain;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final vehicle = captain.vehicle;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 24,
            backgroundColor: AppColors.ink,
            child: Text(
              captain.name.isEmpty ? '?' : captain.name[0].toUpperCase(),
              style: const TextStyle(color: AppColors.brand, fontSize: 20, fontWeight: FontWeight.w800),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(captain.name, style: theme.textTheme.titleMedium),
                const SizedBox(height: 2),
                Row(
                  children: [
                    const Icon(Icons.star_rounded, size: 16, color: AppColors.brandDark),
                    const SizedBox(width: 2),
                    Text(
                      captain.rating == null ? 'New captain' : captain.rating!.toStringAsFixed(1),
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
                if (vehicle != null) ...[
                  const SizedBox(height: 6),
                  Text(
                    vehicle.description.isEmpty ? vehicle.type.label : vehicle.description,
                    style: theme.textTheme.bodySmall,
                  ),
                ],
              ],
            ),
          ),
          if (vehicle != null && vehicle.registrationNumber.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: AppColors.brand,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.ink, width: 1.2),
              ),
              child: Text(
                vehicle.registrationNumber,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, letterSpacing: 0.5),
              ),
            ),
        ],
      ),
    );
  }
}
