import 'package:flutter/material.dart';
import '../features/onboarding/onboarding_screen.dart';
import '../features/permissions/permission_privacy_screen.dart';
import '../features/navigation/main_navigation_screen.dart';
import '../features/scan/text_scan_screen.dart';
import '../features/scan/url_scan_screen.dart';
import '../features/scan/qr_scan_screen.dart';
import '../features/result/result_screen.dart';
import '../features/live_protection/live_protection_screen.dart';

class AppRoutes {
  AppRoutes._();

  static const String onboarding = '/onboarding';
  static const String permissions = '/permissions';
  static const String main = '/main';
  static const String textScan = '/scan/text';
  static const String urlScan = '/scan/url';
  static const String qrScan = '/scan/qr';
  static const String result = '/result';
  static const String liveProtection = '/live-protection';

  static Map<String, WidgetBuilder> get routes => {
        onboarding: (_) => const OnboardingScreen(),
        permissions: (_) => const PermissionPrivacyScreen(),
        main: (_) => const MainNavigationScreen(),
        textScan: (_) => const TextScanScreen(),
        urlScan: (_) => const UrlScanScreen(),
        qrScan: (_) => const QrScanScreen(),
        result: (_) => const ResultScreen(),
        liveProtection: (_) => const LiveProtectionScreen(),
      };
}
