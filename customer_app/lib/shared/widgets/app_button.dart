import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';

enum AppButtonVariant { ink, brand, outline }

/// Full-width action button. [ink] is the main CTA, [brand] is the yellow accent.
class AppButton extends StatelessWidget {
  const AppButton({
    super.key,
    required this.label,
    this.onPressed,
    this.loading = false,
    this.variant = AppButtonVariant.ink,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool loading;
  final AppButtonVariant variant;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final spinnerColor = variant == AppButtonVariant.ink ? AppColors.onInk : AppColors.ink;
    final child = loading
        ? SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2.4, color: spinnerColor),
          )
        : Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (icon != null) ...[Icon(icon, size: 20), const SizedBox(width: 8)],
              Text(label, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            ],
          );

    final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(14));
    final disabledStyle = ButtonStyle(
      shape: WidgetStatePropertyAll(shape),
      minimumSize: const WidgetStatePropertyAll(Size(double.infinity, 56)),
    );

    final button = switch (variant) {
      AppButtonVariant.ink => FilledButton(
          onPressed: loading ? null : onPressed,
          style: disabledStyle.copyWith(
            backgroundColor: const WidgetStatePropertyAll(AppColors.ink),
            foregroundColor: const WidgetStatePropertyAll(AppColors.onInk),
          ),
          child: child,
        ),
      AppButtonVariant.brand => FilledButton(
          onPressed: loading ? null : onPressed,
          style: disabledStyle.copyWith(
            backgroundColor: const WidgetStatePropertyAll(AppColors.brand),
            foregroundColor: const WidgetStatePropertyAll(AppColors.ink),
          ),
          child: child,
        ),
      AppButtonVariant.outline => OutlinedButton(
          onPressed: loading ? null : onPressed,
          style: disabledStyle.copyWith(
            side: const WidgetStatePropertyAll(BorderSide(color: AppColors.ink, width: 1.2)),
            foregroundColor: const WidgetStatePropertyAll(AppColors.ink),
          ),
          child: child,
        ),
    };

    return SizedBox(width: double.infinity, child: button);
  }
}
