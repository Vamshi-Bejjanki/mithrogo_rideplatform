import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../app/theme/app_colors.dart';
import '../../../core/location/mock_places.dart';
import '../../../core/location/place.dart';
import '../application/booking_controller.dart';

/// Pickup and drop search, like the "Where to?" screen in Uber and Rapido.
/// Tap the pickup to change it, or type in the drop field to search destinations.
class LocationSearchScreen extends ConsumerStatefulWidget {
  const LocationSearchScreen({super.key});

  @override
  ConsumerState<LocationSearchScreen> createState() => _LocationSearchScreenState();
}

class _LocationSearchScreenState extends ConsumerState<LocationSearchScreen> {
  late final TextEditingController _pickupController;
  late final TextEditingController _dropController;
  bool _editingDrop = true;

  @override
  void initState() {
    super.initState();
    final booking = ref.read(bookingControllerProvider);
    _pickupController = TextEditingController(text: booking.pickup?.name ?? 'Current location');
    _dropController = TextEditingController(text: booking.drop?.name ?? '');
  }

  @override
  void dispose() {
    _pickupController.dispose();
    _dropController.dispose();
    super.dispose();
  }

  void _selectPlace(Place place) {
    final notifier = ref.read(bookingControllerProvider.notifier);
    if (_editingDrop) {
      // Fares load on the home screen; no need to wait for them here.
      notifier.setDrop(place);
      context.pop();
      return;
    }
    notifier.setPickup(place);
    setState(() {
      _pickupController.text = place.name;
      _editingDrop = true;
    });
  }

  void _useCurrentLocation() {
    ref.read(bookingControllerProvider.notifier).useCurrentLocationForPickup();
    setState(() {
      _pickupController.text = 'Current location';
      _editingDrop = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _editingDrop ? _dropController.text.trim().toLowerCase() : '';
    final results = mockPlaces.where((place) {
      return query.isEmpty ||
          place.name.toLowerCase().contains(query) ||
          place.address.toLowerCase().contains(query);
    }).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Plan your ride')),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(18),
                  boxShadow: const [BoxShadow(color: Colors.black12, blurRadius: 12, offset: Offset(0, 4))],
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
                        Container(width: 2, height: 28, color: AppColors.divider),
                        Container(width: 10, height: 10, color: AppColors.ink),
                      ],
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        children: [
                          _FieldRow(
                            controller: _pickupController,
                            hint: 'Pickup',
                            readOnly: true,
                            active: !_editingDrop,
                            onTap: () => setState(() => _editingDrop = false),
                          ),
                          const Divider(height: 1),
                          _FieldRow(
                            controller: _dropController,
                            hint: 'Where to?',
                            active: _editingDrop,
                            onTap: () => setState(() => _editingDrop = true),
                            onChanged: (_) => setState(() {}),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Expanded(
              child: ListView(
                children: [
                  if (!_editingDrop)
                    ListTile(
                      leading: const Icon(Icons.my_location, color: AppColors.ink),
                      title: const Text('Use current location'),
                      subtitle: const Text('Your device location'),
                      onTap: _useCurrentLocation,
                    ),
                  if (results.isEmpty)
                    Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(
                        'No places match "${_dropController.text.trim()}".',
                        textAlign: TextAlign.center,
                        style: theme.textTheme.bodySmall,
                      ),
                    ),
                  for (final place in results)
                    ListTile(
                      leading: Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.place_outlined, color: AppColors.ink, size: 20),
                      ),
                      title: Text(place.name, style: theme.textTheme.bodyLarge),
                      subtitle: Text(place.address, style: theme.textTheme.bodySmall),
                      onTap: () => _selectPlace(place),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FieldRow extends StatelessWidget {
  const _FieldRow({
    required this.controller,
    required this.hint,
    required this.active,
    required this.onTap,
    this.readOnly = false,
    this.onChanged,
  });

  final TextEditingController controller;
  final String hint;
  final bool active;
  final VoidCallback onTap;
  final bool readOnly;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: AbsorbPointer(
        absorbing: readOnly,
        child: TextField(
          controller: controller,
          readOnly: readOnly,
          onTap: onTap,
          onChanged: onChanged,
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                fontWeight: active ? FontWeight.w700 : FontWeight.w500,
              ),
          decoration: InputDecoration(
            hintText: hint,
            filled: false,
            border: InputBorder.none,
            enabledBorder: InputBorder.none,
            focusedBorder: InputBorder.none,
            contentPadding: const EdgeInsets.symmetric(vertical: 12),
          ),
        ),
      ),
    );
  }
}
