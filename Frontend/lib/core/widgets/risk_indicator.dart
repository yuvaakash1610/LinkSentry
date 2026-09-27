import 'package:flutter/material.dart';
import '../../models/risk_assessment.dart';
import '../constants/app_colors.dart';
import '../constants/app_typography.dart';
import 'risk_badge.dart';

class RiskIndicator extends StatelessWidget {
  final int score;
  final RiskLevel level;
  final String? summary;

  const RiskIndicator({
    super.key,
    required this.score,
    required this.level,
    this.summary,
  });

  @override
  Widget build(BuildContext context) {
    Color ringColor;
    Color containerBg;
    IconData heroIcon;

    switch (level) {
      case RiskLevel.lowRisk:
        ringColor = AppColors.riskLowText;
        containerBg = AppColors.riskLowContainer.withValues(alpha: 0.3);
        heroIcon = Icons.shield_rounded;
        break;
      case RiskLevel.verifyIndependently:
        ringColor = AppColors.riskVerifyText;
        containerBg = AppColors.riskVerifyContainer.withValues(alpha: 0.3);
        heroIcon = Icons.shield_moon_rounded;
        break;
      case RiskLevel.suspicious:
        ringColor = AppColors.riskSuspiciousText;
        containerBg = AppColors.riskSuspiciousContainer.withValues(alpha: 0.3);
        heroIcon = Icons.warning_amber_rounded;
        break;
      case RiskLevel.highRisk:
        ringColor = AppColors.riskHighText;
        containerBg = AppColors.riskHighContainer.withValues(alpha: 0.3);
        heroIcon = Icons.gpp_bad_rounded;
        break;
    }

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(24),
        boxShadow: AppColors.cardShadow,
      ),
      child: Column(
        children: [
          Stack(
            alignment: Alignment.center,
            children: [
              // Outer Progress Ring
              SizedBox(
                width: 140,
                height: 140,
                child: CircularProgressIndicator(
                  value: score / 100.0,
                  strokeWidth: 12,
                  backgroundColor: AppColors.surfaceContainerHigh,
                  valueColor: AlwaysStoppedAnimation<Color>(ringColor),
                  strokeCap: StrokeCap.round,
                ),
              ),
              // Inner Tonal Badge
              Container(
                width: 108,
                height: 108,
                decoration: BoxDecoration(
                  color: containerBg,
                  shape: BoxShape.circle,
                ),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(heroIcon, size: 28, color: ringColor),
                    const SizedBox(height: 2),
                    Text(
                      '$score%',
                      style: AppTypography.headlineMedium.copyWith(
                        fontWeight: FontWeight.w800,
                        color: ringColor,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          RiskBadge(level: level, isLarge: true),
          if (summary != null) ...[
            const SizedBox(height: 12),
            Text(
              summary!,
              textAlign: TextAlign.center,
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.onSurfaceVariant,
                height: 1.4,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
