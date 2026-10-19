import '../constants/app_constants.dart';

// Same rule as backend/apps/users/phone.py: E.164, e.g. +919812345678.
final _e164Pattern = RegExp(r'^\+[1-9]\d{7,14}$');
final _tenDigitPattern = RegExp(r'^\d{10}$');

/// Returns the phone number in E.164 form, or null if it isn't valid.
///
/// Spaces, dashes and brackets are removed first. A bare 10-digit number is
/// treated as an Indian number and gets the default country code.
String? normalizePhone(String raw) {
  final cleaned = raw.replaceAll(RegExp(r'[\s\-()]'), '');
  if (_tenDigitPattern.hasMatch(cleaned)) {
    return '${AppConstants.defaultCountryCode}$cleaned';
  }
  return _e164Pattern.hasMatch(cleaned) ? cleaned : null;
}
