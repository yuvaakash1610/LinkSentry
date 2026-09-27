import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_strings.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/app_button.dart';
import '../../core/widgets/risk_indicator.dart';
import '../../models/risk_reason.dart';
import '../../state/app_state_provider.dart';

class ResultScreen extends StatelessWidget {
  const ResultScreen({super.key});

  void _showFeedbackDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Report / Feedback'),
        content: const Text(
          'Was this risk assessment accurate? Your feedback improves local threat heuristic models.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(dialogCtx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Thank you for your feedback!')),
              );
            },
            child: const Text('Accurate'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(dialogCtx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                    content: Text('Feedback logged for model tuning.')),
              );
            },
            child: const Text('False Positive'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStateProvider>(
      builder: (context, state, _) {
        final result = state.currentResult;

        if (result == null) {
          return Scaffold(
            appBar: AppBar(title: const Text('Analysis Result')),
            body: const Center(child: Text('No active analysis result found.')),
          );
        }

        final assessment = result.assessment;

        return Scaffold(
          backgroundColor: AppColors.surface,
          appBar: AppBar(
            title: const Text('Security Assessment'),
            backgroundColor: AppColors.surface,
            elevation: 0,
            actions: [
              IconButton(
                icon: const Icon(Icons.share_outlined),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                        content: Text('Sharing risk report summary...')),
                  );
                },
              ),
            ],
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. Hero Risk Indicator Dial
                  RiskIndicator(
                    score: assessment.score,
                    level: assessment.level,
                    summary: assessment.summary,
                  ),

                  const SizedBox(height: 20),

                  // 2. Extracted Target Domain (if present)
                  if (result.extractedDomain != null) ...[
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceContainerLowest,
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: AppColors.surfaceContainerHigh),
                      ),
                      child: Row(
                        children: [
                          Container(
                            width: 36,
                            height: 36,
                            decoration: BoxDecoration(
                              color: AppColors.secondaryContainer,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.public_rounded,
                              size: 18,
                              color: AppColors.primary,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'FLAGGED DOMAIN / TARGET',
                                  style: AppTypography.labelSmall.copyWith(
                                    color: AppColors.outline,
                                  ),
                                ),
                                Text(
                                  result.extractedDomain!,
                                  style: AppTypography.titleMedium.copyWith(
                                    color: AppColors.primaryContainer,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],

                  // 3. Reasons for Assessment
                  Text(
                    'Reasons for Assessment',
                    style: AppTypography.titleLarge.copyWith(
                      color: AppColors.onSurface,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 10),

                  Column(
                    children: assessment.reasons
                        .map((reason) => _ReasonCard(reason: reason))
                        .toList(),
                  ),

                  const SizedBox(height: 20),

                  // 4. Recommended Actions
                  Text(
                    'Recommended Safety Actions',
                    style: AppTypography.titleLarge.copyWith(
                      color: AppColors.onSurface,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 10),

                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.surfaceContainerHigh),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: Column(
                      children: assessment.recommendedActions
                          .map((action) => _ActionRow(action: action))
                          .toList(),
                    ),
                  ),

                  const SizedBox(height: 20),

                  // 5. Disclaimer Notice
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLow,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.surfaceContainerHigh),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Icon(
                          Icons.info_outline_rounded,
                          size: 18,
                          color: AppColors.primary,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            AppStrings.riskDisclaimer,
                            style: AppTypography.bodySmall.copyWith(
                              color: AppColors.onSurfaceVariant,
                              height: 1.35,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  // 6. Action buttons
                  Row(
                    children: [
                      Expanded(
                        child: AppButton(
                          label: 'Scan Again',
                          variant: ButtonVariant.outlined,
                          onPressed: () {
                            Navigator.of(context).pop();
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: AppButton(
                          label: 'Done',
                          onPressed: () {
                            state.clearResult();
                            Navigator.of(context).popUntil((route) => route.isFirst);
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),

                  Center(
                    child: TextButton.icon(
                      icon: const Icon(Icons.flag_outlined, size: 16),
                      label: const Text('Report / Submit Feedback'),
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.secondary,
                      ),
                      onPressed: () => _showFeedbackDialog(context),
                    ),
                  ),

                  const SizedBox(height: 16),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _ReasonCard extends StatelessWidget {
  final RiskReason reason;

  const _ReasonCard({required this.reason});

  @override
  Widget build(BuildContext context) {
    Color iconBg;
    Color iconColor;

    switch (reason.severity) {
      case RiskSeverity.low:
        iconBg = AppColors.riskLowContainer;
        iconColor = AppColors.riskLowText;
        break;
      case RiskSeverity.medium:
        iconBg = AppColors.riskVerifyContainer;
        iconColor = AppColors.riskVerifyText;
        break;
      case RiskSeverity.high:
        iconBg = AppColors.riskSuspiciousContainer;
        iconColor = AppColors.riskSuspiciousText;
        break;
      case RiskSeverity.critical:
        iconBg = AppColors.riskHighContainer;
        iconColor = AppColors.riskHighText;
        break;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.surfaceContainerHigh),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: iconBg,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.error_outline_rounded,
              size: 18,
              color: iconColor,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  reason.title,
                  style: AppTypography.titleMedium.copyWith(
                    fontSize: 15,
                    color: AppColors.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  reason.description,
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.onSurfaceVariant,
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionRow extends StatelessWidget {
  final String action;

  const _ActionRow({required this.action});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.check_circle_rounded,
            size: 18,
            color: AppColors.riskLowText,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              action,
              style: AppTypography.bodyMedium.copyWith(
                color: AppColors.onSurface,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
