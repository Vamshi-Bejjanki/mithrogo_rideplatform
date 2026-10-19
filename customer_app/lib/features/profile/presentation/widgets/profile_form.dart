import 'package:flutter/material.dart';

import '../../../../core/network/api_exception.dart';
import '../../../../core/utils/phone_utils.dart';
import '../../../../shared/widgets/app_button.dart';
import '../../models/customer_profile.dart';
import '../../models/profile_input.dart';

final _emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

/// Shared by signup and edit profile. Shows API errors under the button.
class ProfileForm extends StatefulWidget {
  const ProfileForm({
    super.key,
    required this.submitLabel,
    required this.onSubmit,
    this.initial,
  });

  final String submitLabel;
  final CustomerProfile? initial;
  final Future<void> Function(ProfileInput input) onSubmit;

  @override
  State<ProfileForm> createState() => _ProfileFormState();
}

class _ProfileFormState extends State<ProfileForm> {
  final _formKey = GlobalKey<FormState>();
  late final _firstName = TextEditingController(text: widget.initial?.firstName ?? '');
  late final _lastName = TextEditingController(text: widget.initial?.lastName ?? '');
  late final _email = TextEditingController(text: widget.initial?.email ?? '');
  late final _emergencyName = TextEditingController(text: widget.initial?.emergencyContactName ?? '');
  late final _emergencyPhone = TextEditingController(text: widget.initial?.emergencyContactPhone ?? '');

  bool _saving = false;
  String? _error;

  @override
  void dispose() {
    for (final controller in [_firstName, _lastName, _email, _emergencyName, _emergencyPhone]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await widget.onSubmit(ProfileInput(
        firstName: _firstName.text.trim(),
        lastName: _lastName.text.trim(),
        email: _email.text.trim(),
        emergencyContactName: _emergencyName.text.trim(),
        emergencyContactPhone: _emergencyPhone.text.trim().isEmpty
            ? ''
            : (normalizePhone(_emergencyPhone.text) ?? ''),
      ));
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _firstName,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(labelText: 'First name *'),
            validator: (value) =>
                (value == null || value.trim().isEmpty) ? 'Enter your first name.' : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _lastName,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(labelText: 'Last name'),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email'),
            validator: (value) {
              final text = value?.trim() ?? '';
              if (text.isEmpty || _emailPattern.hasMatch(text)) return null;
              return 'Enter a valid email address.';
            },
          ),
          const SizedBox(height: 24),
          Text('Emergency contact (optional)', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 12),
          TextFormField(
            controller: _emergencyName,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(labelText: 'Name'),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _emergencyPhone,
            keyboardType: TextInputType.phone,
            decoration: const InputDecoration(labelText: 'Phone', hintText: '+919812345678'),
            validator: (value) {
              final text = value?.trim() ?? '';
              if (text.isEmpty || normalizePhone(text) != null) return null;
              return 'Use international format, e.g. +919812345678.';
            },
          ),
          const SizedBox(height: 24),
          if (_error != null) ...[
            Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            const SizedBox(height: 12),
          ],
          AppButton(label: widget.submitLabel, loading: _saving, onPressed: _submit),
        ],
      ),
    );
  }
}
