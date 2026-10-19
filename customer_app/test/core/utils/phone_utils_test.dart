import 'package:flutter_test/flutter_test.dart';
import 'package:customer_app/core/utils/phone_utils.dart';

void main() {
  group('normalizePhone', () {
    test('accepts E.164 and strips separators', () {
      expect(normalizePhone('+91 98123-45678'), '+919812345678');
    });

    test('adds the default country code to a bare 10-digit number', () {
      expect(normalizePhone('9812345678'), '+919812345678');
    });

    test('rejects anything else', () {
      expect(normalizePhone('abc'), isNull);
      expect(normalizePhone('+0123456789'), isNull);
      expect(normalizePhone('12345'), isNull);
    });
  });
}
