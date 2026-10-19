import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../app/router.dart';
import '../../../../app/theme/app_colors.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../../../shared/widgets/app_button.dart';
import '../../../booking/application/booking_controller.dart';
import '../../../ride/application/ride_providers.dart';
import '../../../ride/models/ride_options.dart';
import '../../../../shared/widgets/sheet_container.dart';
import 'vehicle_option_tile.dart';

/// Shown once a destination is chosen: route, ride options, payment, and the book button.
class BookingSheet extends ConsumerStatefulWidget {
  const BookingSheet({super.key});

  @override
  ConsumerState<BookingSheet> createState() => _BookingSheetState();
}

class _BookingSheetState extends ConsumerState<BookingSheet> {
  bool _booking = false;

  Future<void> _book() async {
    setState(() => _booking = true);
    try {
      final rideId = await ref.read(bookingControllerProvider.notifier).book();
      ref.invalidate(rideHistoryProvider);
      if (!mounted) return;
      context.go(AppRoutes.rideDetail(rideId));
    } on ApiException catch (error) {
      if (error.code == 'active_ride_exists') {
        await _openActiveRide();
      } else {
        _showMessage(error.message);
      }
    } catch (error) {
      _showMessage(userMessage(error));
    } finally {
      if (mounted) setState(() => _booking = false);
    }
  }

  /// The backend allows one active ride per customer. Take them to it instead of a dead end.
  Future<void> _openActiveRide() async {
    ref.invalidate(rideHistoryProvider);
    final active = await ref.read(activeRideProvider.future).catchError((_) => null);
    if (!mounted) return;
    if (active == null) {
      _showMessage('You already have a ride in progress.');
      return;
    }
    _showMessage('You already have a ride in progress.');
    context.go(AppRoutes.rideDetail(active.id));
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final booking = ref.watch(bookingControllerProvider);
    final notifier = ref.read(bookingControllerProvider.notifier);
    final selected = booking.selectedEstimate;

    return SheetContainer(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _RouteCard(
            pickup: booking.pickup?.name ?? 'Current location',
            drop: booking.drop?.name ?? '',
            onChange: () => context.push(AppRoutes.search),
            onClear: notifier.clearDrop,
          ),
          const SizedBox(height: 16),
          Text('Choose a ride', style: theme.textTheme.titleMedium),
          const SizedBox(height: 10),
          for (final vehicle in VehicleType.values) ...[
            VehicleOptionTile(
              vehicle: vehicle,
              estimate: booking.estimates[vehicle],
              selected: booking.vehicle == vehicle,
              onTap: () => notifier.selectVehicle(vehicle),
            ),
            const SizedBox(height: 8),
          ],
          if (booking.estimating) ...[
            const SizedBox(height: 4),
            const LinearProgressIndicator(minHeight: 2, color: AppColors.ink),
            const SizedBox(height: 8),
          ],
          if (booking.error != null) ...[
            Row(
              children: [
                Expanded(child: Text(booking.error!, style: const TextStyle(color: AppColors.danger))),
                TextButton(onPressed: notifier.retryEstimates, child: const Text('Retry')),
              ],
            ),
            const SizedBox(height: 8),
          ],
          const SizedBox(height: 4),
          SegmentedButton<PaymentMethod>(
            segments: const [
              ButtonSegment(
                value: PaymentMethod.cash,
                icon: Icon(Icons.payments_outlined),
                label: Text('Cash'),
              ),
              ButtonSegment(
                value: PaymentMethod.online,
                icon: Icon(Icons.qr_code_2),
                label: Text('UPI / Card'),
              ),
            ],
            selected: {booking.payment},
            showSelectedIcon: false,
            onSelectionChanged: (selection) => notifier.selectPayment(selection.first),
          ),
          const SizedBox(height: 16),
          AppButton(
            variant: AppButtonVariant.brand,
            label: selected == null
                ? 'Book ${booking.vehicle.label}'
                : 'Book ${booking.vehicle.label} · ${formatInr(selected.fare)}',
            loading: _booking,
            onPressed: booking.canBook && !_booking ? _book : null,
          ),
        ],
      ),
    );
  }
}

class _RouteCard extends StatelessWidget {
  const _RouteCard({
    required this.pickup,
    required this.drop,
    required this.onChange,
    required this.onClear,
  });

  final String pickup;
  final String drop;
  final VoidCallback onChange;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.fromLTRB(14, 12, 4, 12),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Column(
            children: [
              Container(
                width: 10,
                height: 10,
                decoration: const BoxDecoration(color: AppColors.ink, shape: BoxShape.circle),
              ),
              Container(width: 2, height: 22, color: AppColors.divider),
              Container(width: 10, height: 10, color: AppColors.ink),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(pickup, maxLines: 1, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodySmall),
                const SizedBox(height: 10),
                Text(
                  drop,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w700),
                ),
              ],
            ),
          ),
          TextButton(onPressed: onChange, child: const Text('Change')),
          IconButton(
            tooltip: 'Clear destination',
            onPressed: onClear,
            icon: const Icon(Icons.close, size: 20),
          ),
        ],
      ),
    );
  }
}
