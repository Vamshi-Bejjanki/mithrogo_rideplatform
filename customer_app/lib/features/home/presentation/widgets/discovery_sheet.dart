import 'package:flutter/material.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/location/mock_places.dart';
import '../../../../core/location/place.dart';
import '../../../../shared/widgets/sheet_container.dart';

/// Shown before a destination is chosen: greeting, search, and recent places.
class DiscoverySheet extends StatelessWidget {
  const DiscoverySheet({
    super.key,
    required this.firstName,
    required this.onSearchTap,
    required this.onPlaceTap,
  });

  final String firstName;
  final VoidCallback onSearchTap;
  final ValueChanged<Place> onPlaceTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final recent = mockPlaces.take(3).toList();

    return SheetContainer(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            firstName.isEmpty ? 'Where to?' : 'Hi $firstName, where to?',
            style: theme.textTheme.headlineMedium,
          ),
          const SizedBox(height: 16),
          InkWell(
            borderRadius: BorderRadius.circular(14),
            onTap: onSearchTap,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Row(
                children: [
                  const Icon(Icons.search, color: AppColors.ink),
                  const SizedBox(width: 12),
                  Text('Search destination', style: theme.textTheme.bodyLarge?.copyWith(
                        color: AppColors.textSecondary,
                      )),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          for (final place in recent)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(Icons.history, color: AppColors.ink, size: 20),
              ),
              title: Text(place.name, style: theme.textTheme.bodyLarge),
              subtitle: Text(
                place.address,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodySmall,
              ),
              onTap: () => onPlaceTap(place),
            ),
        ],
      ),
    );
  }
}
