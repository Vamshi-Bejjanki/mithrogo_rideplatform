import 'package:customer_app/app/providers.dart';
import 'package:customer_app/core/storage/token_storage.dart';
import 'package:customer_app/features/auth/application/session_controller.dart';
import 'package:customer_app/features/splash/presentation/splash_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

/// No saved tokens, and no platform keystore needed.
class _EmptyTokenStorage extends TokenStorage {
  @override
  Future<String?> readAccessToken() async => null;

  @override
  Future<String?> readRefreshToken() async => null;
}

void main() {
  testWidgets('shows the brand and signs out only after the minimum splash time', (tester) async {
    final container = ProviderContainer(
      overrides: [tokenStorageProvider.overrideWithValue(_EmptyTokenStorage())],
    );
    addTearDown(container.dispose);

    await tester.pumpWidget(UncontrolledProviderScope(
      container: container,
      child: const MaterialApp(home: SplashScreen()),
    ));
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.byIcon(Icons.two_wheeler), findsOneWidget);
    expect(find.bySemanticsLabel('MithroGo'), findsOneWidget);
    expect(container.read(sessionControllerProvider).status, SessionStatus.unknown);

    await tester.pump(SplashScreen.minimumDuration);
    await tester.pump();
    expect(container.read(sessionControllerProvider).status, SessionStatus.signedOut);
  });
}
