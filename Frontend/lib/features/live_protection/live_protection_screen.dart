import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/app_button.dart';
import '../../core/widgets/privacy_disclaimer_card.dart';
import '../../core/widgets/setting_tile.dart';
import '../../state/app_state_provider.dart';

class LiveProtectionScreen extends StatelessWidget {
  const LiveProtectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStateProvider>(
      builder: (context, state, _) {
        final live = state.liveProtection;
        final isPermissionGranted = live.notificationPermissionGranted;
        final isEnabled = live.isEnabled;

        final availableApps = [
          {'name': 'Messages', 'icon': Icons.message_rounded},
          {'name': 'WhatsApp', 'icon': Icons.chat_bubble_rounded},
          {'name': 'Telegram', 'icon': Icons.send_rounded},
          {'name': 'Email', 'icon': Icons.email_rounded},
        ];

        return Scaffold(
          backgroundColor: AppColors.surface,
          appBar: AppBar(
            title: const Text('Live Safeguard Settings'),
            backgroundColor: AppColors.surface,
            elevation: 0,
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Main Live Protection Hero Card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(
                        color: isEnabled
                            ? AppColors.primaryContainer
                            : AppColors.surfaceContainerHighest,
                        width: isEnabled ? 2 : 1,
                      ),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 48,
                          height: 48,
                          decoration: BoxDecoration(
                            color: isEnabled
                                ? AppColors.primaryContainer
                                : AppColors.secondaryContainer,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            isEnabled
                                ? Icons.shield_rounded
                                : Icons.shield_outlined,
                            color: isEnabled
                                ? Colors.white
                                : AppColors.secondary,
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Live Protection',
                                style: AppTypography.titleLarge.copyWith(
                                  color: AppColors.onSurface,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                              Text(
                                isEnabled
                                    ? 'Actively inspecting notification previews'
                                    : 'Live protection disabled',
                                style: AppTypography.bodySmall.copyWith(
                                  color: isEnabled
                                      ? AppColors.riskLowText
                                      : AppColors.outline,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ),
                        Switch(
                          value: isEnabled,
                          activeTrackColor: AppColors.primaryContainer,
                          onChanged: (val) {
                            state.toggleLiveProtection(val);
                          },
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Notification Permission Status Section
                  Text(
                    'Android Notification Access',
                    style: AppTypography.titleLarge.copyWith(
                      color: AppColors.onSurface,
                    ),
                  ),
                  const SizedBox(height: 8),
                  SettingTile(
                    icon: isPermissionGranted
                        ? Icons.check_circle_rounded
                        : Icons.warning_amber_rounded,
                    iconColor: isPermissionGranted
                        ? AppColors.riskLowText
                        : AppColors.error,
                    title: 'System Access Status',
                    subtitle: isPermissionGranted
                        ? 'Connected & Authorized'
                        : 'Not Connected — Permission required for live alerts',
                    trailing: isPermissionGranted
                        ? Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppColors.riskLowContainer,
                              borderRadius: BorderRadius.circular(9999),
                            ),
                            child: Text(
                              'Connected',
                              style: AppTypography.labelSmall.copyWith(
                                color: AppColors.riskLowText,
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          )
                        : TextButton(
                            onPressed: () =>
                                state.requestNotificationPermission(),
                            child: const Text('Grant'),
                          ),
                  ),

                  const SizedBox(height: 20),

                  // Selected Monitored Apps Checklist
                  Text(
                    'Monitored Applications',
                    style: AppTypography.titleLarge.copyWith(
                      color: AppColors.onSurface,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'LinkSentry will only inspect notification previews from apps you select below:',
                    style: AppTypography.bodyMedium.copyWith(
                      color: AppColors.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 12),

                  Column(
                    children: availableApps.map((app) {
                      final name = app['name'] as String;
                      final icon = app['icon'] as IconData;
                      final isSelected = live.monitoredApps.contains(name);

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: SettingTile(
                          icon: icon,
                          title: name,
                          subtitle: isSelected
                              ? 'Active monitoring'
                              : 'Disabled for this app',
                          trailing: Checkbox(
                            value: isSelected,
                            activeColor: AppColors.primaryContainer,
                            onChanged: (_) {
                              state.toggleMonitoredApp(name);
                            },
                          ),
                          onTap: () {
                            state.toggleMonitoredApp(name);
                          },
                        ),
                      );
                    }).toList(),
                  ),

                  const SizedBox(height: 20),

                  const PrivacyDisclaimerCard(),

                  const SizedBox(height: 24),

                  if (isEnabled)
                    AppButton(
                      label: 'Disable Live Protection',
                      variant: ButtonVariant.outlined,
                      onPressed: () {
                        state.toggleLiveProtection(false);
                      },
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
