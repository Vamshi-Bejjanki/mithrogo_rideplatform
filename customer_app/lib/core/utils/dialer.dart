import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

/// India's single emergency number (police, fire, ambulance).
const emergencyNumber = '112';

/// Opens the phone dialer with [number] filled in. Returns false if no dialer is available.
Future<bool> openDialer(String number) async {
  try {
    return await launchUrl(Uri(scheme: 'tel', path: number));
  } on PlatformException {
    return false;
  }
}
