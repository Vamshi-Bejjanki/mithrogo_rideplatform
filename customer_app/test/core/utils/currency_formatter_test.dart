import 'package:flutter_test/flutter_test.dart';
import 'package:customer_app/core/utils/currency_formatter.dart';

void main() {
  group('formatInr', () {
    test('keeps two decimals', () {
      expect(formatInr('62.72'), '₹62.72');
    });

    test('pads missing decimals', () {
      expect(formatInr('62'), '₹62.00');
      expect(formatInr('62.5'), '₹62.50');
    });

    test('uses Indian digit grouping', () {
      expect(formatInr('1000'), '₹1,000.00');
      expect(formatInr('123456'), '₹1,23,456.00');
      expect(formatInr('1234567.5'), '₹12,34,567.50');
    });

    test('handles a leading zero', () {
      expect(formatInr('0.5'), '₹0.50');
    });
  });
}
