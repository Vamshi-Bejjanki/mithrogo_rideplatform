import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';

/// Friendly empty state. Scrollable, so it works inside a RefreshIndicator.
class EmptyView extends StatelessWidget {
  const EmptyView({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.action,
  });

  final IconData icon;
  final String title;
  final String message;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(32, 96, 32, 32),
      children: [
        Center(
          child: Container(
            width: 88,
            height: 88,
            decoration: const BoxDecoration(color: AppColors.card, shape: BoxShape.circle),
            child: Icon(icon, size: 40, color: AppColors.ink),
          ),
        ),
        const SizedBox(height: 20),
        Text(title, textAlign: TextAlign.center, style: theme.textTheme.titleMedium),
        const SizedBox(height: 6),
        Text(message, textAlign: TextAlign.center, style: theme.textTheme.bodySmall),
        if (action != null) ...[
          const SizedBox(height: 20),
          action!,
        ],
      ],
    );
  }
}
