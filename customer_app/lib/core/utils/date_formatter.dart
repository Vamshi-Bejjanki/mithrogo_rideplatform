const _months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

/// "15 Oct 2026". Local time, no time-of-day.
String formatDate(DateTime date) => '${date.day} ${_months[date.month - 1]} ${date.year}';

/// "15 Oct 2026, 09:05". Local time.
String formatDateTime(DateTime date) {
  final hh = date.hour.toString().padLeft(2, '0');
  final mm = date.minute.toString().padLeft(2, '0');
  return '${formatDate(date)}, $hh:$mm';
}
