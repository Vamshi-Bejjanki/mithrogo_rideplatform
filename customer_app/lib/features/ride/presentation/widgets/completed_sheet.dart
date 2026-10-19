import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../app/config/flavors.dart';
import '../../../../app/providers.dart';
import '../../../../app/router.dart';
import '../../../../app/theme/app_colors.dart';
import '../../../../core/network/api_exception.dart';
import '../../../../core/utils/currency_formatter.dart';
import '../../../../shared/widgets/app_button.dart';
import '../../../../shared/widgets/sheet_container.dart';
import '../../application/ride_providers.dart';
import '../../models/ride.dart';
import '../../models/ride_payment.dart';

/// Fare receipt plus a rating form, shown after the ride completes.
class CompletedSheet extends ConsumerStatefulWidget {
  const CompletedSheet({super.key, required this.rideId});

  final String rideId;

  @override
  ConsumerState<CompletedSheet> createState() => _CompletedSheetState();
}

class _CompletedSheetState extends ConsumerState<CompletedSheet> {
  final _commentController = TextEditingController();
  int _rating = 0;
  bool _submitting = false;
  bool _submitted = false;
  String? _error;

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      await ref.read(rideRepositoryProvider).rate(
            widget.rideId,
            rating: _rating,
            comment: _commentController.text.trim(),
          );
      if (mounted) setState(() => _submitted = true);
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final detail = ref.watch(rideDetailProvider(widget.rideId));

    return SheetContainer(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('You have arrived', style: theme.textTheme.headlineMedium),
          const SizedBox(height: 4),
          Text('Thanks for riding with us.', style: theme.textTheme.bodySmall),
          const SizedBox(height: 16),
          detail.when(
            loading: () => const LinearProgressIndicator(minHeight: 2, color: AppColors.ink),
            error: (error, _) => Text(userMessage(error), style: const TextStyle(color: AppColors.danger)),
            data: (ride) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _Receipt(ride: ride),
                if (ride.needsOnlinePayment) ...[
                  const SizedBox(height: 12),
                  _PaySection(rideId: widget.rideId, fare: ride.displayFare),
                ],
              ],
            ),
          ),
          const SizedBox(height: 20),
          if (_submitted)
            Text('Rating sent. Thank you!', style: theme.textTheme.titleMedium)
          else ...[
            Text('How was your ride?', style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            _StarPicker(
              value: _rating,
              onChanged: (value) => setState(() => _rating = value),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _commentController,
              maxLength: 500,
              minLines: 1,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: 'Add a comment (optional)',
                counterText: '',
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(_error!, style: const TextStyle(color: AppColors.danger)),
            ],
            const SizedBox(height: 12),
            AppButton(
              label: 'Submit rating',
              loading: _submitting,
              onPressed: _rating > 0 && !_submitting ? _submit : null,
            ),
          ],
          const SizedBox(height: 8),
          AppButton(
            variant: _submitted ? AppButtonVariant.ink : AppButtonVariant.outline,
            label: _submitted ? 'Done' : 'Skip for now',
            onPressed: () => context.go(AppRoutes.home),
          ),
        ],
      ),
    );
  }
}

class _Receipt extends StatelessWidget {
  const _Receipt({required this.ride});

  final Ride ride;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final method = ride.isOnline ? 'UPI / Card' : 'Cash';
    final paid = ride.isOnline ? '$method · ${ride.isPaid ? 'Paid' : 'Due'}' : method;
    final distance = ride.estimatedDistanceKm == null
        ? '--'
        : '${ride.estimatedDistanceKm!.toStringAsFixed(1)} km';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Total fare', style: theme.textTheme.bodyLarge),
              Text(
                formatInr(ride.displayFare),
                style: theme.textTheme.headlineMedium,
              ),
            ],
          ),
          const SizedBox(height: 12),
          _ReceiptRow(label: 'Distance', value: distance),
          _ReceiptRow(label: 'Payment', value: paid),
          _ReceiptRow(label: 'Ride type', value: ride.vehicleType.label),
        ],
      ),
    );
  }
}

class _ReceiptRow extends StatelessWidget {
  const _ReceiptRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: theme.textTheme.bodySmall),
          Text(value, style: theme.textTheme.bodyLarge),
        ],
      ),
    );
  }
}

class _StarPicker extends StatelessWidget {
  const _StarPicker({required this.value, required this.onChanged});

  final int value;
  final ValueChanged<int> onChanged;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        for (var star = 1; star <= 5; star++)
          IconButton(
            iconSize: 36,
            tooltip: '$star star${star == 1 ? '' : 's'}',
            onPressed: () => onChanged(star),
            icon: Icon(
              star <= value ? Icons.star_rounded : Icons.star_outline_rounded,
              color: star <= value ? AppColors.brand : AppColors.textSecondary,
            ),
          ),
      ],
    );
  }
}

/// Pay for a completed ONLINE ride. The backend creates a gateway order; the ride is marked
/// paid only when the gateway webhook confirms it, so the customer checks back for the result.
class _PaySection extends ConsumerStatefulWidget {
  const _PaySection({required this.rideId, required this.fare});

  final String rideId;
  final String fare;

  @override
  ConsumerState<_PaySection> createState() => _PaySectionState();
}

class _PaySectionState extends ConsumerState<_PaySection> {
  RidePayment? _payment;
  bool _busy = false;
  String? _message;

  Future<void> _run(Future<void> Function() action) async {
    setState(() {
      _busy = true;
      _message = null;
    });
    try {
      await action();
    } on ApiException catch (error) {
      if (mounted) setState(() => _message = error.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _startPayment() => _run(() async {
        final payment = await ref.read(rideRepositoryProvider).pay(widget.rideId);
        if (mounted) setState(() => _payment = payment);
      });

  Future<void> _checkStatus() => _run(() async {
        final payment = await ref.read(rideRepositoryProvider).payment(_payment!.id);
        if (!mounted) return;
        setState(() {
          _payment = payment;
          if (payment.isFailed) _message = 'The payment failed. Please try again.';
          if (!payment.isPaid && !payment.isFailed) _message = 'Still waiting for the bank to confirm.';
        });
        if (payment.isPaid) ref.invalidate(rideDetailProvider(widget.rideId));
      });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final payment = _payment;

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.brand.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.brand),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Icon(Icons.qr_code_2, color: AppColors.ink),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  payment == null ? 'Payment due' : 'Waiting for payment confirmation',
                  style: theme.textTheme.titleMedium,
                ),
              ),
            ],
          ),
          if (payment != null) ...[
            const SizedBox(height: 6),
            Text('Order ${payment.providerOrderId}', style: theme.textTheme.bodySmall),
            if (!Flavors.isProd)
              Text(
                'Dev: run "python manage.py simulate_payment ${payment.providerOrderId}"',
                style: theme.textTheme.bodySmall?.copyWith(fontSize: 11),
              ),
          ],
          if (_message != null) ...[
            const SizedBox(height: 6),
            Text(_message!, style: theme.textTheme.bodySmall?.copyWith(color: AppColors.inkSoft)),
          ],
          const SizedBox(height: 12),
          AppButton(
            variant: AppButtonVariant.ink,
            loading: _busy,
            label: payment == null ? 'Pay ${formatInr(widget.fare)}' : 'Check payment status',
            onPressed: payment == null ? _startPayment : _checkStatus,
          ),
        ],
      ),
    );
  }
}
