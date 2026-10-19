import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/providers.dart';
import '../../../app/router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/utils/dialer.dart';
import '../../../shared/widgets/app_button.dart';
import '../../ride/application/ride_providers.dart';
import '../../support/models/support_ticket.dart';

/// Safety centre: call 112, call the saved emergency contact, or alert our safety team
/// about the ride in progress (a SAFETY support ticket linked to that ride).
class EmergencyScreen extends ConsumerStatefulWidget {
  const EmergencyScreen({super.key});

  @override
  ConsumerState<EmergencyScreen> createState() => _EmergencyScreenState();
}

class _EmergencyScreenState extends ConsumerState<EmergencyScreen> {
  bool _reporting = false;

  Future<void> _call(String number) async {
    final opened = await openDialer(number);
    if (!opened && mounted) _show('Could not open the dialer. Please call $number directly.');
  }

  Future<void> _alertSafetyTeam(String? rideId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Alert the safety team?'),
        content: Text(
          rideId == null
              ? 'Our safety team will be notified and will contact you.'
              : 'Our safety team will be notified about your current ride and will contact you.',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Not now')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Send alert'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;

    setState(() => _reporting = true);
    try {
      await ref.read(supportRepositoryProvider).create(
            category: TicketCategory.safety,
            description: rideId == null
                ? 'SOS raised from the safety centre in the customer app.'
                : 'SOS raised from the safety centre during an active ride.',
            rideId: rideId,
          );
      _show('Safety team alerted. Stay on a call with someone you trust.');
    } on ApiException catch (error) {
      _show(error.message);
    } finally {
      if (mounted) setState(() => _reporting = false);
    }
  }

  void _show(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final profile = ref.watch(customerProfileProvider).valueOrNull;
    final activeRide = ref.watch(activeRideProvider).valueOrNull;
    final hasContact = (profile?.emergencyContactPhone ?? '').isNotEmpty;

    return Scaffold(
      appBar: AppBar(title: const Text('Safety centre')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppColors.danger,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.sos_rounded, color: AppColors.onInk, size: 32),
                    SizedBox(width: 10),
                    Text(
                      'Emergency',
                      style: TextStyle(color: AppColors.onInk, fontSize: 22, fontWeight: FontWeight.w800),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                const Text(
                  'If you feel unsafe, call emergency services first.',
                  style: TextStyle(color: AppColors.onInk, fontSize: 14),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.onInk,
                      foregroundColor: AppColors.danger,
                      minimumSize: const Size.fromHeight(52),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                    onPressed: () => _call(emergencyNumber),
                    icon: const Icon(Icons.call),
                    label: const Text(
                      'Call $emergencyNumber',
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _Section(
            title: 'Emergency contact',
            action: TextButton(
              onPressed: () => context.push(AppRoutes.editProfile),
              child: Text(hasContact ? 'Edit' : 'Add contact'),
            ),
            child: hasContact
                ? ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const CircleAvatar(
                      backgroundColor: AppColors.brand,
                      child: Icon(Icons.person, color: AppColors.ink),
                    ),
                    title: Text(
                      profile!.emergencyContactName.isEmpty ? 'Emergency contact' : profile.emergencyContactName,
                      style: theme.textTheme.bodyLarge,
                    ),
                    subtitle: Text(profile.emergencyContactPhone, style: theme.textTheme.bodySmall),
                    trailing: IconButton.filled(
                      style: IconButton.styleFrom(backgroundColor: AppColors.ink),
                      tooltip: 'Call contact',
                      onPressed: () => _call(profile.emergencyContactPhone),
                      icon: const Icon(Icons.call, color: AppColors.onInk),
                    ),
                  )
                : Text(
                    'Add someone we can help you reach quickly in an emergency.',
                    style: theme.textTheme.bodySmall,
                  ),
          ),
          const SizedBox(height: 16),
          _Section(
            title: 'Safety team',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  activeRide == null
                      ? 'Report a safety concern. Our team will reach out to you.'
                      : 'You have a ride in progress. The alert will include its details.',
                  style: theme.textTheme.bodySmall,
                ),
                const SizedBox(height: 12),
                AppButton(
                  variant: AppButtonVariant.outline,
                  icon: Icons.shield_outlined,
                  label: 'Alert safety team',
                  loading: _reporting,
                  onPressed: () => _alertSafetyTeam(activeRide?.id),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title, this.action, required this.child});

  final String title;
  final Widget child;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
      decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(child: Text(title, style: Theme.of(context).textTheme.titleMedium)),
              ?action,
            ],
          ),
          if (action == null) const SizedBox(height: 8),
          child,
        ],
      ),
    );
  }
}
