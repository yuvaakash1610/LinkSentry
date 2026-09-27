import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_strings.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/history_card.dart';
import '../../core/widgets/privacy_disclaimer_card.dart';
import '../../core/widgets/section_header.dart';
import '../../core/widgets/security_status_card.dart';
import '../../core/widgets/scan_option_card.dart';
import '../../state/app_state_provider.dart';
import '../live_protection/live_protection_screen.dart';
import '../result/result_screen.dart';
import '../scan/text_scan_screen.dart';
import '../scan/url_scan_screen.dart';
import '../scan/qr_scan_screen.dart';

class HomeDashboardScreen extends StatelessWidget {
  const HomeDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStateProvider>(
      builder: (context, state, _) {
        final recentHistory = state.history.take(3).toList();

        return Scaffold(
          backgroundColor: AppColors.surface,
          appBar: AppBar(
            backgroundColor: AppColors.surface,
            elevation: 0,
            title: Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    color: AppColors.primaryContainer,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.shield_rounded,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 10),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      AppStrings.appName,
                      style: AppTypography.titleLarge.copyWith(
                        color: AppColors.primary,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    Text(
                      AppStrings.tagline,
                      style: AppTypography.labelSmall.copyWith(
                        color: AppColors.outline,
                        fontSize: 10,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.shield_moon_rounded),
                color: AppColors.primary,
                tooltip: 'Live Safeguard',
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const LiveProtectionScreen(),
                    ),
                  );
                },
              ),
              const SizedBox(width: 8),
            ],
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Security Status Card
                SecurityStatusCard(
                  isLiveProtectionOn: state.liveProtection.isEnabled,
                  onTapLiveProtection: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => const LiveProtectionScreen(),
                      ),
                    );
                  },
                ),

                const SizedBox(height: 20),

                // 2. Primary Scan Actions
                const SectionHeader(title: 'Scan & Verify'),
                ScanOptionCard(
                  title: 'Scan Message / SMS',
                  description:
                      'Paste copied SMS, WhatsApp texts, or email alerts',
                  icon: Icons.sms_outlined,
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => const TextScanScreen(),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 10),
                ScanOptionCard(
                  title: 'Scan Link / Web Address',
                  description: 'Inspect suspicious links before clicking',
                  icon: Icons.link_rounded,
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => const UrlScanScreen(),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 10),
                ScanOptionCard(
                  title: 'Scan QR Destination',
                  description: 'Scan QR codes safely without auto-opening',
                  icon: Icons.qr_code_scanner_rounded,
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => const QrScanScreen(),
                      ),
                    );
                  },
                ),

                const SizedBox(height: 20),

                // 3. Privacy Assurance Note
                const PrivacyDisclaimerCard(),

                const SizedBox(height: 20),

                // 4. Recent Scans
                SectionHeader(
                  title: 'Recent Scans',
                  actionLabel:
                      recentHistory.isNotEmpty ? 'View All History' : null,
                  onActionTap: () {
                    state.setTabIndex(2); // History Tab
                  },
                ),
                if (recentHistory.isEmpty)
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.surfaceContainerHigh),
                    ),
                    child: Center(
                      child: Text(
                        'No scan history yet. Tap a scan option above to check a message or link.',
                        style: AppTypography.bodySmall.copyWith(
                          color: AppColors.outline,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  )
                else
                  Column(
                    children: recentHistory
                        .map(
                          (item) => Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: HistoryCard(
                              item: item,
                              onTap: () {
                                // Re-trigger analysis / result view for this item
                                if (item.domain != null) {
                                  state.analyzeUrl('https://${item.domain}');
                                } else {
                                  state.analyzeText(item.title);
                                }
                                Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) => const ResultScreen(),
                                  ),
                                );
                              },
                              onDelete: () => state.deleteHistoryItem(item.id),
                            ),
                          ),
                        )
                        .toList(),
                  ),

                const SizedBox(height: 24),
              ],
            ),
          ),
        );
      },
    );
  }
}
