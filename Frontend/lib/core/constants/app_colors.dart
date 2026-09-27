import 'package:flutter/material.dart';

/// LinkSentry Design System - Color Tokens
/// Based directly on Stitch.ai design specification
class AppColors {
  AppColors._();

  // Baseline Tonal Palette
  static const Color primary = Color(0xFF004E5A);
  static const Color primaryContainer = Color(0xFF006877);
  static const Color onPrimary = Color(0xFFFFFFFF);
  static const Color onPrimaryContainer = Color(0xFF98E4F5);
  static const Color primaryFixed = Color(0xFFA4EEFF);
  static const Color onPrimaryFixed = Color(0xFF001F25);

  static const Color secondary = Color(0xFF4A6267);
  static const Color secondaryContainer = Color(0xFFCDE7ED);
  static const Color onSecondaryContainer = Color(0xFF50686D);
  static const Color secondaryFixed = Color(0xFFCDE7ED);
  static const Color onSecondaryFixed = Color(0xFF051F23);

  static const Color tertiary = Color(0xFF3A4664);
  static const Color tertiaryContainer = Color(0xFF525E7D);
  static const Color onTertiaryContainer = Color(0xFFCCD8FD);

  static const Color background = Color(0xFFF9F9F9);
  static const Color surface = Color(0xFFF9F9F9);
  static const Color surfaceDim = Color(0xFFD9DADA);
  static const Color surfaceBright = Color(0xFFF9F9F9);

  // Surface Tiers
  static const Color surfaceContainerLowest = Color(0xFFFFFFFF);
  static const Color surfaceContainerLow = Color(0xFFF3F4F3);
  static const Color surfaceContainer = Color(0xFFEDEEEE);
  static const Color surfaceContainerHigh = Color(0xFFE8E8E8);
  static const Color surfaceContainerHighest = Color(0xFFE2E3E2);

  // Contrast Tiers
  static const Color onSurface = Color(0xFF1A1C1C);
  static const Color onSurfaceVariant = Color(0xFF3F484B);
  static const Color outline = Color(0xFF6F797B);
  static const Color outlineVariant = Color(0xFFBEC8CB);

  // Risk System Tonal Pairs
  // 1. Low Risk (0 - 29)
  static const Color riskLowText = Color(0xFF146C2E);
  static const Color riskLowContainer = Color(0xFFD1F0D9);
  static const Color riskLowIcon = Color(0xFF146C2E);

  // 2. Verify Independently (30 - 59)
  static const Color riskVerifyText = Color(0xFF7D5700);
  static const Color riskVerifyContainer = Color(0xFFFFE082);
  static const Color riskVerifyIcon = Color(0xFF7D5700);

  // 3. Suspicious (60 - 79)
  static const Color riskSuspiciousText = Color(0xFF8F4C00);
  static const Color riskSuspiciousContainer = Color(0xFFFFDCBE);
  static const Color riskSuspiciousIcon = Color(0xFF8F4C00);

  // 4. High Risk (80 - 100)
  static const Color riskHighText = Color(0xFFBA1A1A);
  static const Color riskHighContainer = Color(0xFFFFDAD6);
  static const Color riskHighIcon = Color(0xFFBA1A1A);

  // Errors
  static const Color error = Color(0xFFBA1A1A);
  static const Color onError = Color(0xFFFFFFFF);
  static const Color errorContainer = Color(0xFFFFDAD6);
  static const Color onErrorContainer = Color(0xFF93000A);

  // Shadows
  static List<BoxShadow> get cardShadow => [
        BoxShadow(
          color: const Color(0xFF006877).withValues(alpha: 0.06),
          blurRadius: 8,
          offset: const Offset(0, 2),
        ),
        BoxShadow(
          color: Colors.black.withValues(alpha: 0.04),
          blurRadius: 3,
          offset: const Offset(0, 1),
        ),
      ];

  static List<BoxShadow> get floatingShadow => [
        BoxShadow(
          color: const Color(0xFF001F25).withValues(alpha: 0.12),
          blurRadius: 32,
          offset: const Offset(0, 12),
        ),
      ];
}
