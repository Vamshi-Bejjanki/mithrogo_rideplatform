import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../app/providers.dart';
import '../../../app/theme/app_colors.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_exception.dart';
import '../../../shared/widgets/app_button.dart';
import '../application/session_controller.dart';

class OtpScreen extends ConsumerStatefulWidget {
  const OtpScreen({super.key, required this.phone});

  final String phone;

  @override
  ConsumerState<OtpScreen> createState() => _OtpScreenState();
}

class _OtpScreenState extends ConsumerState<OtpScreen> {
  final _codeController = TextEditingController();
  bool _verifying = false;
  String? _error;

  static const _resendWait = 30;
  int _resendIn = _resendWait;
  Timer? _resendTimer;

  @override
  void initState() {
    super.initState();
    _startResendTimer();
  }

  @override
  void dispose() {
    _resendTimer?.cancel();
    _codeController.dispose();
    super.dispose();
  }

  void _startResendTimer() {
    _resendTimer?.cancel();
    _resendIn = _resendWait;
    _resendTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) return timer.cancel();
      setState(() => _resendIn--);
      if (_resendIn <= 0) timer.cancel();
    });
  }

  Future<void> _verify() async {
    final code = _codeController.text.trim();
    if (code.length != AppConstants.otpLength) {
      setState(() => _error = 'Enter the ${AppConstants.otpLength}-digit code.');
      return;
    }

    setState(() {
      _verifying = true;
      _error = null;
    });
    try {
      // On success the session changes and the router moves to home or profile setup.
      await ref.read(sessionControllerProvider.notifier).verifyOtp(
            phone: widget.phone,
            code: code,
          );
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    } finally {
      if (mounted) setState(() => _verifying = false);
    }
  }

  Future<void> _resend() async {
    try {
      await ref.read(authRepositoryProvider).sendOtp(widget.phone);
      if (!mounted) return;
      setState(_startResendTimer);
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(const SnackBar(content: Text('A new code is on its way.')));
    } on ApiException catch (error) {
      if (mounted) setState(() => _error = error.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final code = _codeController.text;

    return Scaffold(
      appBar: AppBar(),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Enter the code', style: theme.textTheme.displaySmall),
              const SizedBox(height: 8),
              Text.rich(
                TextSpan(
                  style: theme.textTheme.bodySmall,
                  children: [
                    const TextSpan(text: 'We sent a ${AppConstants.otpLength}-digit code to '),
                    TextSpan(
                      text: widget.phone,
                      style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 32),
              // Six boxes drawn over a hidden text field, which does the real input.
              Stack(
                alignment: Alignment.center,
                children: [
                  Row(
                    children: List.generate(AppConstants.otpLength, (index) {
                      final filled = index < code.length;
                      final focused = index == code.length;
                      return Expanded(
                        child: Padding(
                          padding: EdgeInsets.only(left: index == 0 ? 0 : 8),
                          child: AspectRatio(
                            aspectRatio: 0.85,
                            child: Container(
                              alignment: Alignment.center,
                              decoration: BoxDecoration(
                                color: AppColors.card,
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(
                                  color: focused ? AppColors.ink : AppColors.divider,
                                  width: focused ? 1.8 : 1,
                                ),
                              ),
                              child: Text(
                                filled ? code[index] : '',
                                style: theme.textTheme.headlineMedium,
                              ),
                            ),
                          ),
                        ),
                      );
                    }),
                  ),
                  Positioned.fill(
                    child: Opacity(
                      opacity: 0,
                      child: TextField(
                        controller: _codeController,
                        autofocus: true,
                        keyboardType: TextInputType.number,
                        maxLength: AppConstants.otpLength,
                        inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                        autofillHints: const [AutofillHints.oneTimeCode],
                        decoration: const InputDecoration(
                          counterText: '',
                          border: InputBorder.none,
                          filled: false,
                        ),
                        onChanged: (value) {
                          setState(() => _error = null);
                          // Submit as soon as the last digit is typed (or autofilled).
                          if (value.length == AppConstants.otpLength && !_verifying) _verify();
                        },
                        onSubmitted: (_) => _verify(),
                      ),
                    ),
                  ),
                ],
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: AppColors.danger)),
              ],
              const SizedBox(height: 24),
              AppButton(label: 'Verify & continue', loading: _verifying, onPressed: _verify),
              const SizedBox(height: 8),
              Center(
                child: TextButton(
                  onPressed: _resendIn > 0 ? null : _resend,
                  child: Text(_resendIn > 0 ? 'Resend code in ${_resendIn}s' : 'Resend code'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
