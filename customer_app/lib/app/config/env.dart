/// Build-time configuration. Override per build with --dart-define.
///
/// Example: flutter run --dart-define=API_BASE_URL=https://api.example.com/api/v1/
class Env {
  const Env._();

  /// Default points at the Django dev server from an Android emulator.
  /// iOS simulators and desktop use http://127.0.0.1:8000/api/v1/ instead.
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1/',
  );
}
