import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_strings.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/privacy_disclaimer_card.dart';
import '../../core/widgets/section_header.dart';
import '../../core/widgets/setting_tile.dart';
import '../../state/app_state_provider.dart';
import '../live_protection/live_protection_screen.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStateProvider>(
      builder: (context, state, _) {
        final live = state.liveProtection;
        final privacy = state.privacySettings;

        return Scaffold(
          backgroundColor: AppColors.surface,
          appBar: AppBar(
            title: const Text('Settings & Privacy'),
            backgroundColor: AppColors.surface,
            elevation: 0,
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Security Section
                  const SectionHeader(title: 'Security'),
                  SettingTile(
                    icon: Icons.shield_rounded,
                    title: 'Live Protection',
                    subtitle: live.isEnabled
                        ? 'Active — Monitoring notification previews'
                        : 'Disabled',
                    trailing: Switch(
                      value: live.isEnabled,
                      activeTrackColor: AppColors.primaryContainer,
                      onChanged: (val) {
                        state.toggleLiveProtection(val);
                      },
                    ),
                    onTap: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const LiveProtectionScreen(),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 8),
                  SettingTile(
                    icon: Icons.notifications_active_rounded,
                    title: 'Notification Access',
                    subtitle: live.notificationPermissionGranted
                        ? 'Granted & Active'
                        : 'Not Granted — Tap to connect',
                    onTap: () {
                      state.requestNotificationPermission();
                    },
                  ),

                  const SizedBox(height: 16),

                  // Privacy Section
                  const SectionHeader(title: 'Privacy & Data'),
                  SettingTile(
                    icon: Icons.phonelink_lock_rounded,
                    title: 'Device-Local Inspection',
                    subtitle:
                        'Text is analyzed locally and never stored remotely',
                    trailing: Switch(
                      value: privacy.localAnalysisOnly,
                      activeTrackColor: AppColors.primaryContainer,
                      onChanged: (val) {
                        state.updatePrivacySettings(
                          privacy.copyWith(localAnalysisOnly: val),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 8),
                  SettingTile(
                    icon: Icons.history_rounded,
                    title: 'Save Raw Messages in History',
                    subtitle: privacy.storeRawMessagesInHistory
                        ? 'Enabled'
                        : 'Disabled (Result summaries only)',
                    trailing: Switch(
                      value: privacy.storeRawMessagesInHistory,
                      activeTrackColor: AppColors.primaryContainer,
                      onChanged: (val) {
                        state.updatePrivacySettings(
                          privacy.copyWith(storeRawMessagesInHistory: val),
                        );
                      },
                    ),
                  ),
                  const SizedBox(height: 8),
                  SettingTile(
                    icon: Icons.delete_forever_rounded,
                    iconColor: AppColors.error,
                    title: 'Clear Scan History',
                    subtitle: 'Permanently remove all saved local scan items',
                    onTap: () async {
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder: (dCtx) => AlertDialog(
                          title: const Text('Clear History?'),
                          content: const Text(
                              'This will permanently remove all scan summaries saved on this device.'),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(dCtx, false),
                              child: const Text('Cancel'),
                            ),
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: AppColors.error,
                              ),
                              onPressed: () => Navigator.pop(dCtx, true),
                              child: const Text('Clear All'),
                            ),
                          ],
                        ),
                      );
                      if (confirm == true) {
                        await state.clearAllHistory();
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Scan history cleared.'),
                            ),
                          );
                        }
                      }
                    },
                  ),

                  const SizedBox(height: 16),

                  const PrivacyDisclaimerCard(),

                  const SizedBox(height: 16),

                  // Support & About Section
                  const SectionHeader(title: 'Support & App Info'),
                  SettingTile(
                    icon: Icons.language_rounded,
                    title: 'App Language',
                    subtitle: 'English (Default)',
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('Language selection: English'),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 8),
                  SettingTile(
                    icon: Icons.help_outline_rounded,
                    title: 'Help & Support',
                    subtitle: 'FAQs, CyberCell helpline, & feedback',
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('National Cyber Crime Helpline: 1930'),
                        ),
                      );
                    },
                  ),
                  const SizedBox(height: 8),
                  SettingTile(
                    icon: Icons.info_outline_rounded,
                    title: 'About LinkSentry',
                    subtitle: 'Version 1.0.0 (Production Build)',
                  ),

                  const SizedBox(height: 24),

                  // Footer Branding
                  Center(
                    child: Column(
                      children: [
                        Text(
                          AppStrings.appName,
                          style: AppTypography.titleMedium.copyWith(
                            color: AppColors.primary,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          AppStrings.tagline,
                          style: AppTypography.bodySmall.copyWith(
                            color: AppColors.outline,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          '© 2026 LinkSentry Security. All rights reserved.',
                          style: AppTypography.labelSmall.copyWith(
                            color: AppColors.outline,
                            fontSize: 10,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
