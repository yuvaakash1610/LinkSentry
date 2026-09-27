import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/app_button.dart';
import '../../core/widgets/privacy_disclaimer_card.dart';
import '../../state/app_state_provider.dart';
import '../navigation/main_navigation_screen.dart';

class PermissionPrivacyScreen extends StatelessWidget {
  const PermissionPrivacyScreen({super.key});

  void _navigateToMain(BuildContext context) async {
    final state = Provider.of<AppStateProvider>(context, listen: false);
    await state.completeOnboarding();
    if (context.mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const MainNavigationScreen()),
        (route) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        title: const Text('Live Protection & Privacy'),
        backgroundColor: AppColors.surface,
        elevation: 0,
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Top Icon
                    Center(
                      child: Container(
                        width: 72,
                        height: 72,
                        decoration: BoxDecoration(
                          color: AppColors.secondaryContainer,
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.notifications_active_rounded,
                          size: 36,
                          color: AppColors.primary,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Center(
                      child: Text(
                        'Live Safeguard Permission',
                        style: AppTypography.headlineSmall.copyWith(
                          color: AppColors.onSurface,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Center(
                      child: Text(
                        'Optional automatic protection for incoming messages',
                        style: AppTypography.bodyMedium.copyWith(
                          color: AppColors.onSurfaceVariant,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(height: 24),

                    const PrivacyDisclaimerCard(),
                    const SizedBox(height: 20),

                    Text(
                      'Why LinkSentry Needs Access',
                      style: AppTypography.titleLarge.copyWith(
                        color: AppColors.onSurface,
                      ),
                    ),
                    const SizedBox(height: 10),
                    const _PermissionInfoRow(
                      icon: Icons.check_circle_outline_rounded,
                      iconColor: AppColors.riskLowText,
                      title: 'What LinkSentry Analyzes',
                      description:
                          'Incoming notification previews from selected messaging apps (e.g. SMS, WhatsApp) to check for phishing links.',
                    ),
                    const SizedBox(height: 12),
                    const _PermissionInfoRow(
                      icon: Icons.do_not_disturb_on_outlined,
                      iconColor: AppColors.error,
                      title: 'What LinkSentry NEVER Does',
                      description:
                          'Does NOT read personal chats, does NOT transmit text to remote servers, and does NOT run background keylogging.',
                    ),
                    const SizedBox(height: 12),
                    const _PermissionInfoRow(
                      icon: Icons.tune_rounded,
                      iconColor: AppColors.primary,
                      title: 'Full User Control',
                      description:
                          'You can toggle Live Protection ON or OFF anytime from Settings or Home screen.',
                    ),
                  ],
                ),
              ),
            ),

            // Bottom CTA section
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainerLowest,
                boxShadow: AppColors.cardShadow,
              ),
              child: Column(
                children: [
                  AppButton(
                    label: 'Enable Live Protection',
                    icon: Icons.security_rounded,
                    onPressed: () async {
                      final state =
                          Provider.of<AppStateProvider>(context, listen: false);
                      await state.requestNotificationPermission();
                      await state.toggleLiveProtection(true);
                      if (context.mounted) _navigateToMain(context);
                    },
                  ),
                  const SizedBox(height: 10),
                  AppButton(
                    label: 'Skip for Now (Manual Scan Mode)',
                    variant: ButtonVariant.outlined,
                    onPressed: () => _navigateToMain(context),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _PermissionInfoRow extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String title;
  final String description;

  const _PermissionInfoRow({
    required this.icon,
    required this.iconColor,
    required this.title,
    required this.description,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.surfaceContainerHigh),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: iconColor, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: AppTypography.titleMedium.copyWith(
                    fontSize: 15,
                    color: AppColors.onSurface,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  description,
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
