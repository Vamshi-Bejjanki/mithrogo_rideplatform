import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/empty_view.dart';
import '../../../shared/widgets/error_view.dart';
import '../../../shared/widgets/loading_view.dart';
import '../../ride/application/ride_providers.dart';
import '../models/support_ticket.dart';

final supportTicketsProvider = FutureProvider.autoDispose<List<SupportTicket>>((ref) {
  return ref.watch(supportRepositoryProvider).list();
});

/// Help and support: the customer's tickets, and a form to raise a new one.
class SupportScreen extends ConsumerWidget {
  const SupportScreen({super.key, this.rideId});

  /// Pre-selects a ride when support is opened from a ride.
  final String? rideId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final tickets = ref.watch(supportTicketsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Help and support')),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: AppColors.ink,
        foregroundColor: AppColors.onInk,
        onPressed: () => _newTicket(context),
        icon: const Icon(Icons.add_comment_outlined),
        label: const Text('Raise a ticket'),
      ),
      body: RefreshIndicator(
        color: AppColors.ink,
        onRefresh: () => ref.refresh(supportTicketsProvider.future),
        child: tickets.when(
          loading: () => const LoadingView(),
          error: (error, _) => ErrorView(
            scrollable: true,
            message: userMessage(error),
            onRetry: () => ref.invalidate(supportTicketsProvider),
          ),
          data: (items) {
            if (items.isEmpty) {
              return const EmptyView(
                icon: Icons.support_agent_rounded,
                title: 'How can we help?',
                message: 'Raise a ticket about a ride, a payment, safety or your account. '
                    'Our team usually replies within a day.',
              );
            }
            return ListView.separated(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              itemCount: items.length,
              separatorBuilder: (_, _) => const SizedBox(height: 10),
              itemBuilder: (_, index) => _TicketCard(ticket: items[index]),
            );
          },
        ),
      ),
    );
  }

  Future<void> _newTicket(BuildContext context) async {
    final created = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      backgroundColor: AppColors.card,
      builder: (_) => NewTicketForm(initialRideId: rideId),
    );
    if (created == true && context.mounted) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(const SnackBar(content: Text('Ticket raised. We will get back to you soon.')));
    }
  }
}

class _TicketCard extends StatelessWidget {
  const _TicketCard({required this.ticket});

  final SupportTicket ticket;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final (background, foreground) = ticket.isOpen
        ? (AppColors.brand, AppColors.ink)
        : (AppColors.success.withValues(alpha: 0.12), AppColors.success);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: AppColors.card, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '#${ticket.id} · ${ticket.category.label}',
                  style: theme.textTheme.titleMedium,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: background, borderRadius: BorderRadius.circular(999)),
                child: Text(
                  ticket.statusLabel,
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: foreground),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(ticket.description, maxLines: 3, overflow: TextOverflow.ellipsis, style: theme.textTheme.bodyLarge),
          if (ticket.resolutionNote.isNotEmpty) ...[
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: AppColors.surface, borderRadius: BorderRadius.circular(12)),
              child: Text('Support: ${ticket.resolutionNote}', style: theme.textTheme.bodySmall),
            ),
          ],
          if (ticket.createdAt != null) ...[
            const SizedBox(height: 8),
            Text(formatDateTime(ticket.createdAt!), style: theme.textTheme.bodySmall?.copyWith(fontSize: 12)),
          ],
        ],
      ),
    );
  }
}

/// Bottom-sheet form. Pops with `true` once the ticket is created.
class NewTicketForm extends ConsumerStatefulWidget {
  const NewTicketForm({super.key, this.initialRideId, this.initialCategory = TicketCategory.rideIssue});

  final String? initialRideId;
  final TicketCategory initialCategory;

  @override
  ConsumerState<NewTicketForm> createState() => _NewTicketFormState();
}

class _NewTicketFormState extends ConsumerState<NewTicketForm> {
  final _description = TextEditingController();
  late TicketCategory _category = widget.initialCategory;
  late String? _rideId = widget.initialRideId;
  bool _sending = false;
  String? _error;

  @override
  void dispose() {
    _description.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final text = _description.text.trim();
    if (text.length < 10) {
      setState(() => _error = 'Tell us a little more (at least 10 characters).');
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      await ref.read(supportRepositoryProvider).create(
            category: _category,
            description: text,
            rideId: _rideId,
          );
      ref.invalidate(supportTicketsProvider);
      if (mounted) Navigator.of(context).pop(true);
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final rides = ref.watch(rideHistoryProvider).valueOrNull ?? const [];
    final recentRides = rides.take(10).toList();

    return Padding(
      padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Raise a ticket', style: theme.textTheme.headlineMedium),
            const SizedBox(height: 16),
            Text('What is it about?', style: theme.textTheme.bodySmall),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final category in TicketCategory.values)
                  ChoiceChip(
                    label: Text(category.label),
                    selected: _category == category,
                    selectedColor: AppColors.brand,
                    showCheckmark: false,
                    onSelected: (_) => setState(() => _category = category),
                  ),
              ],
            ),
            if (recentRides.isNotEmpty) ...[
              const SizedBox(height: 16),
              DropdownButtonFormField<String?>(
                initialValue: recentRides.any((ride) => ride.id == _rideId) ? _rideId : null,
                isExpanded: true,
                decoration: const InputDecoration(labelText: 'Related ride (optional)'),
                items: [
                  const DropdownMenuItem<String?>(value: null, child: Text('Not about a ride')),
                  for (final ride in recentRides)
                    DropdownMenuItem<String?>(
                      value: ride.id,
                      child: Text(
                        '${ride.requestedAt == null ? '' : '${formatDate(ride.requestedAt!)} · '}${ride.dropAddress}',
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                ],
                onChanged: (value) => setState(() => _rideId = value),
              ),
            ],
            const SizedBox(height: 16),
            TextField(
              controller: _description,
              minLines: 4,
              maxLines: 6,
              maxLength: 1000,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                hintText: 'Describe what happened',
                alignLabelWithHint: true,
              ),
            ),
            if (_error != null) ...[
              Text(_error!, style: const TextStyle(color: AppColors.danger)),
              const SizedBox(height: 12),
            ],
            const SizedBox(height: 4),
            AppButton(label: 'Submit', loading: _sending, onPressed: _submit),
          ],
        ),
      ),
    );
  }
}
