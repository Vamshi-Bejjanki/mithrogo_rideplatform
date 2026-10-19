import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/router.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/utils/currency_formatter.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../shared/widgets/empty_view.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../ride/application/ride_providers.dart';
import '../../ride/models/ride.dart';
import '../../ride/models/ride_options.dart';
import '../../ride/presentation/widgets/ride_status_chip.dart';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final history = ref.watch(rideHistoryProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Your rides')),
      body: RefreshIndicator(
        color: AppColors.ink,
        onRefresh: () => ref.refresh(rideHistoryProvider.future),
        child: history.when(
          loading: () => const LoadingView(),
          error: (error, _) => ErrorView(
            scrollable: true,
            message: userMessage(error),
            onRetry: () => ref.invalidate(rideHistoryProvider),
          ),
          data: (rides) {
            if (rides.isEmpty) {
              return EmptyView(
                icon: Icons.route_outlined,
                title: 'No rides yet',
                message: 'Your trips will show up here.',
                action: Center(
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(backgroundColor: AppColors.ink),
                    onPressed: () => context.go(AppRoutes.home),
                    icon: const Icon(Icons.search),
                    label: const Text('Book a ride'),
                  ),
                ),
              );
            }
            return ListView.separated(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              itemCount: rides.length,
              separatorBuilder: (_, _) => const SizedBox(height: 12),
              itemBuilder: (context, index) => _RideCard(ride: rides[index]),
            );
          },
        ),
      ),
    );
  }
}

class _RideCard extends StatelessWidget {
  const _RideCard({required this.ride});

  final Ride ride;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final when = ride.requestedAt == null ? '' : formatDateTime(ride.requestedAt!);
    final icon = ride.vehicleType == VehicleType.bike ? Icons.two_wheeler : Icons.local_taxi;

    return Material(
      color: AppColors.card,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => context.push(AppRoutes.rideDetail(ride.id)),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(icon, size: 20, color: AppColors.ink),
                  const SizedBox(width: 8),
                  Expanded(child: Text(when, style: theme.textTheme.bodySmall)),
                  RideStatusChip(status: ride.status),
                ],
              ),
              const SizedBox(height: 12),
              _AddressLine(icon: Icons.circle, text: ride.pickupAddress, small: true),
              const SizedBox(height: 6),
              _AddressLine(icon: Icons.square, text: ride.dropAddress),
              const SizedBox(height: 12),
              Row(
                children: [
                  Text(
                    formatInr(ride.displayFare),
                    style: theme.textTheme.titleMedium,
                  ),
                  const Spacer(),
                  Text(ride.vehicleType.label, style: theme.textTheme.bodySmall),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AddressLine extends StatelessWidget {
  const _AddressLine({required this.icon, required this.text, this.small = false});

  final IconData icon;
  final String text;
  final bool small;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: small ? 8 : 10, color: AppColors.ink),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ),
      ],
    );
  }
}
