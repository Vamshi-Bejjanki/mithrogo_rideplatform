import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/config/env.dart';
import '../../../app/config/flavors.dart';
import '../../../app/theme/app_colors.dart';
import '../../../shared/widgets/primary_card.dart';
import '../../auth/application/session_controller.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  Future<void> _signOut(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Log out?'),
        content: const Text('You will need a new OTP to sign in again.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Log out'),
          ),
        ],
      ),
    );
    if (confirmed == true) await ref.read(sessionControllerProvider.notifier).signOut();
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final phone = ref.watch(sessionControllerProvider).user?.phone ?? '';

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          PrimaryCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Signed in as', style: theme.textTheme.bodySmall),
                const SizedBox(height: 2),
                Text(phone, style: theme.textTheme.bodyLarge),
              ],
            ),
          ),
          if (!Flavors.isProd) ...[
            const SizedBox(height: 12),
            PrimaryCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Environment', style: theme.textTheme.bodySmall),
                  Text(Flavors.title, style: theme.textTheme.bodyLarge),
                  const SizedBox(height: 12),
                  Text('Server', style: theme.textTheme.bodySmall),
                  Text(Env.apiBaseUrl, style: theme.textTheme.bodyLarge),
                ],
              ),
            ),
          ],
          const SizedBox(height: 24),
          OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.danger,
              side: const BorderSide(color: AppColors.danger),
              minimumSize: const Size.fromHeight(52),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
            ),
            onPressed: () => _signOut(context, ref),
            icon: const Icon(Icons.logout),
            label: const Text('Log out'),
          ),
          const SizedBox(height: 24),
          Center(child: Text('${Flavors.appName} · v1.0.0', style: theme.textTheme.bodySmall)),
        ],
      ),
    );
  }
}
