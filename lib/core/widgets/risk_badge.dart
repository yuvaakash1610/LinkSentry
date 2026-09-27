import 'package:flutter/material.dart';
import '../../models/risk_assessment.dart';
import '../constants/app_colors.dart';
import '../constants/app_typography.dart';

class RiskBadge extends StatelessWidget {
  final RiskLevel level;
  final bool isLarge;

  const RiskBadge({
    super.key,
    required this.level,
    this.isLarge = false,
  });

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    IconData icon;

    switch (level) {
      case RiskLevel.lowRisk:
        bg = AppColors.riskLowContainer;
        fg = AppColors.riskLowText;
        icon = Icons.verified_user_rounded;
        break;
      case RiskLevel.verifyIndependently:
        bg = AppColors.riskVerifyContainer;
        fg = AppColors.riskVerifyText;
        icon = Icons.help_outline_rounded;
        break;
      case RiskLevel.suspicious:
        bg = AppColors.riskSuspiciousContainer;
        fg = AppColors.riskSuspiciousText;
        icon = Icons.warning_amber_rounded;
        break;
      case RiskLevel.highRisk:
        bg = AppColors.riskHighContainer;
        fg = AppColors.riskHighText;
        icon = Icons.gpp_maybe_rounded;
        break;
    }

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isLarge ? 14 : 10,
        vertical: isLarge ? 8 : 4,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(9999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: isLarge ? 18 : 14,
            color: fg,
          ),
          SizedBox(width: isLarge ? 6 : 4),
          Text(
            level.label,
            style: isLarge
                ? AppTypography.labelLarge.copyWith(color: fg)
                : AppTypography.labelMedium.copyWith(color: fg),
          ),
        ],
      ),
    );
  }
}
