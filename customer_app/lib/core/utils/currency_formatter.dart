/// Formats a backend money string such as "1234567.5" as "₹12,34,567.50".
///
/// Works on the string rather than a double so no precision is lost.
/// Indian digit grouping: the last three digits, then groups of two.
String formatInr(String amount) {
  final trimmed = amount.trim();
  final negative = trimmed.startsWith('-');
  final unsigned = negative ? trimmed.substring(1) : trimmed;

  final parts = unsigned.split('.');
  final whole = parts[0].isEmpty ? '0' : parts[0];
  final fraction = parts.length > 1 ? parts[1].padRight(2, '0').substring(0, 2) : '00';

  return '${negative ? '-' : ''}₹${_groupIndian(whole)}.$fraction';
}

String _groupIndian(String digits) {
  if (digits.length <= 3) return digits;

  final last3 = digits.substring(digits.length - 3);
  var rest = digits.substring(0, digits.length - 3);
  final groups = <String>[];
  while (rest.length > 2) {
    groups.insert(0, rest.substring(rest.length - 2));
    rest = rest.substring(0, rest.length - 2);
  }
  if (rest.isNotEmpty) groups.insert(0, rest);
  return '${groups.join(',')},$last3';
}
