import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/providers.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../auth/application/session_controller.dart';
import 'widgets/profile_form.dart';

class EditProfileScreen extends ConsumerWidget {
  const EditProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(customerProfileProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Edit profile')),
      body: SafeArea(
        child: profileAsync.when(
          loading: () => const LoadingView(),
          error: (error, _) => ErrorView(
            message: userMessage(error),
            onRetry: () => ref.invalidate(customerProfileProvider),
          ),
          data: (profile) => SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: ProfileForm(
              initial: profile,
              submitLabel: 'Save changes',
              onSubmit: (input) async {
                final updated = await ref.read(profileRepositoryProvider).update(input);
                ref.read(sessionControllerProvider.notifier).applyProfile(updated);
                ref.invalidate(customerProfileProvider);
                if (context.mounted) context.pop();
              },
            ),
          ),
        ),
      ),
    );
  }
}
