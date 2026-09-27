import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_typography.dart';
import '../../core/utils/url_extractor.dart';
import '../../core/widgets/app_button.dart';
import '../../core/widgets/error_state.dart';
import '../../core/widgets/privacy_disclaimer_card.dart';
import '../../state/app_state_provider.dart';
import '../result/result_screen.dart';

class TextScanScreen extends StatefulWidget {
  final String? initialText;

  const TextScanScreen({super.key, this.initialText});

  @override
  State<TextScanScreen> createState() => _TextScanScreenState();
}

class _TextScanScreenState extends State<TextScanScreen> {
  late final TextEditingController _controller;
  int _charCount = 0;
  int _detectedLinkCount = 0;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(
      text: widget.initialText ??
          'Dear customer, your bank account access will be suspended within 24 hours due to unverified KYC. Click here immediately to verify identity: https://sbi-secure-kyc-update.cc/verify or share OTP.',
    );
    _updateMetrics();
  }

  void _updateMetrics() {
    final text = _controller.text;
    setState(() {
      _charCount = text.length;
      _detectedLinkCount = UrlExtractor.extractUrls(text).length;
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _pasteFromClipboard() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (data?.text != null) {
      _controller.text = data!.text!;
      _updateMetrics();
    }
  }

  void _clearText() {
    _controller.clear();
    _updateMetrics();
  }

  void _submitAnalysis() async {
    final state = Provider.of<AppStateProvider>(context, listen: false);
    final result = await state.analyzeText(_controller.text);
    if (result != null && mounted) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => const ResultScreen(),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStateProvider>(
      builder: (context, state, _) {
        return Scaffold(
          backgroundColor: AppColors.surface,
          appBar: AppBar(
            title: const Text('Message Analysis'),
            backgroundColor: AppColors.surface,
            elevation: 0,
            actions: [
              IconButton(
                icon: const Icon(Icons.info_outline_rounded),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text(
                          'LinkSentry inspects text patterns locally to detect scam language and phishing links.'),
                    ),
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
                  // Top info banner
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.secondaryContainer,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(6),
                          decoration: const BoxDecoration(
                            color: AppColors.surfaceContainerLowest,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.verified_user_rounded,
                            size: 18,
                            color: AppColors.primary,
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'LinkSentry inspects text patterns, urgent threats, and concealed links. Text is processed securely and never shared.',
                            style: AppTypography.bodyMedium.copyWith(
                              color: AppColors.onSecondaryContainer,
                              height: 1.35,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 14),

                  // Actions row: Paste & Clear
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      ElevatedButton.icon(
                        onPressed: _pasteFromClipboard,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.secondaryFixed,
                          foregroundColor: AppColors.onSecondaryFixed,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(9999),
                          ),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 14, vertical: 8),
                        ),
                        icon: const Icon(Icons.content_paste_rounded, size: 16),
                        label: Text(
                          'Paste from clipboard',
                          style: AppTypography.labelMedium.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      TextButton.icon(
                        onPressed: _clearText,
                        icon: const Icon(Icons.backspace_outlined, size: 16),
                        label: const Text('Clear'),
                        style: TextButton.styleFrom(
                          foregroundColor: AppColors.secondary,
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 12),

                  // Validation Error Banner if present
                  if (state.errorMessage != null) ...[
                    ErrorStateBanner(
                      message: state.errorMessage!,
                      onDismiss: () => state.clearResult(),
                    ),
                    const SizedBox(height: 12),
                  ],

                  // Text Area Input Card
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLow,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.surfaceContainerHigh),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                const Icon(
                                  Icons.sms_rounded,
                                  size: 16,
                                  color: AppColors.primary,
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  'SMS / MESSAGE PAYLOAD',
                                  style: AppTypography.labelSmall.copyWith(
                                    color: AppColors.secondary,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 1.0,
                                  ),
                                ),
                              ],
                            ),
                            if (_detectedLinkCount > 0)
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: AppColors.errorContainer,
                                  borderRadius: BorderRadius.circular(9999),
                                ),
                                child: Text(
                                  'High Suspicion',
                                  style: AppTypography.labelSmall.copyWith(
                                    color: AppColors.onErrorContainer,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        TextField(
                          controller: _controller,
                          maxLines: 6,
                          maxLength: 2000,
                          onChanged: (_) => _updateMetrics(),
                          style: AppTypography.bodyMedium.copyWith(
                            color: AppColors.onSurface,
                            height: 1.4,
                          ),
                          decoration: InputDecoration(
                            hintText:
                                'Paste text message, email snippet, or suspicious alert here...',
                            hintStyle: AppTypography.bodyMedium.copyWith(
                              color: AppColors.outline,
                            ),
                            border: InputBorder.none,
                            counterText: '',
                          ),
                        ),
                        const Divider(),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                const Icon(
                                  Icons.link_rounded,
                                  size: 16,
                                  color: AppColors.primary,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  '$_detectedLinkCount link${_detectedLinkCount == 1 ? '' : 's'} identified',
                                  style: AppTypography.bodySmall.copyWith(
                                    color: AppColors.onSurfaceVariant,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                            Text(
                              '$_charCount / 2,000 characters',
                              style: AppTypography.bodySmall.copyWith(
                                color: AppColors.outline,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Heuristic Safeguards Card
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.surfaceContainerHigh),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              width: 28,
                              height: 28,
                              decoration: BoxDecoration(
                                color: AppColors.primaryFixed,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.psychology_rounded,
                                size: 16,
                                color: AppColors.onPrimaryFixed,
                              ),
                            ),
                            const SizedBox(width: 10),
                            Text(
                              'Heuristic Safeguards',
                              style: AppTypography.titleMedium.copyWith(
                                color: AppColors.onSurface,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        const _HeuristicBullet(
                          icon: Icons.schedule_rounded,
                          text: 'Checks for artificial urgency & countdowns',
                        ),
                        const SizedBox(height: 8),
                        const _HeuristicBullet(
                          icon: Icons.badge_rounded,
                          text: 'Detects impersonation of major banks & couriers',
                        ),
                        const SizedBox(height: 8),
                        const _HeuristicBullet(
                          icon: Icons.travel_explore_rounded,
                          text: 'Dissects hidden or deceptive URLs',
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Analyze Action Button
                  AppButton(
                    label: 'Analyze Message',
                    icon: Icons.manage_search_rounded,
                    isLoading: state.isAnalyzing,
                    onPressed: _submitAnalysis,
                  ),

                  const SizedBox(height: 14),

                  const PrivacyDisclaimerCard(),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

class _HeuristicBullet extends StatelessWidget {
  final IconData icon;
  final String text;

  const _HeuristicBullet({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 22,
          height: 22,
          decoration: BoxDecoration(
            color: AppColors.secondaryContainer,
            shape: BoxShape.circle,
          ),
          child: Icon(icon, size: 13, color: AppColors.primary),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: AppTypography.bodyMedium.copyWith(
              color: AppColors.onSurfaceVariant,
            ),
          ),
        ),
      ],
    );
  }
}
