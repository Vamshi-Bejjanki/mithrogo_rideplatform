import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../profile/presentation/widgets/profile_form.dart';
import '../application/session_controller.dart';

/// New customers complete their profile here after their first OTP sign-in.
class SignupScreen extends ConsumerWidget {
  const SignupScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Complete your profile'),
        actions: [
          TextButton(
            onPressed: () => ref.read(sessionControllerProvider.notifier).signOut(),
            child: const Text('Sign out'),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: ProfileForm(
            submitLabel: 'Continue',
            onSubmit: (input) async {
              final profile = await ref.read(profileRepositoryProvider).update(input);
              ref.read(sessionControllerProvider.notifier).applyProfile(profile);
            },
          ),
        ),
      ),
    );
  }
}
