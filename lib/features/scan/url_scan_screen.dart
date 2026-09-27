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

class UrlScanScreen extends StatefulWidget {
  final String? initialUrl;

  const UrlScanScreen({super.key, this.initialUrl});

  @override
  State<UrlScanScreen> createState() => _UrlScanScreenState();
}

class _UrlScanScreenState extends State<UrlScanScreen> {
  late final TextEditingController _controller;
  String? _extractedDomain;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(
      text: widget.initialUrl ?? 'https://sbi-secure-kyc-update.cc/verify',
    );
    _updateDomain();
  }

  void _updateDomain() {
    setState(() {
      _extractedDomain = UrlExtractor.extractDomain(_controller.text);
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _pasteClipboard() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (data?.text != null) {
      _controller.text = data!.text!;
      _updateDomain();
    }
  }

  void _clearInput() {
    _controller.clear();
    _updateDomain();
  }

  void _submitAnalysis() async {
    final state = Provider.of<AppStateProvider>(context, listen: false);
    final result = await state.analyzeUrl(_controller.text);
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
            title: const Text('URL & Link Inspection'),
            backgroundColor: AppColors.surface,
            elevation: 0,
          ),
          body: SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Check a link before opening it.',
                    style: AppTypography.headlineSmall.copyWith(
                      color: AppColors.onSurface,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'LinkSentry inspects domain reputation, spoofed brand names, unencrypted connections, and suspicious extensions.',
                    style: AppTypography.bodyMedium.copyWith(
                      color: AppColors.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 20),

                  if (state.errorMessage != null) ...[
                    ErrorStateBanner(
                      message: state.errorMessage!,
                      onDismiss: () => state.clearResult(),
                    ),
                    const SizedBox(height: 12),
                  ],

                  // Continuous Pill Input Container for URL
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLow,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.surfaceContainerHigh),
                      boxShadow: AppColors.cardShadow,
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'TARGET WEB ADDRESS',
                              style: AppTypography.labelSmall.copyWith(
                                color: AppColors.secondary,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.0,
                              ),
                            ),
                            Row(
                              children: [
                                InkWell(
                                  onTap: _pasteClipboard,
                                  borderRadius: BorderRadius.circular(9999),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: AppColors.secondaryFixed,
                                      borderRadius: BorderRadius.circular(9999),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(
                                          Icons.content_paste_rounded,
                                          size: 14,
                                          color: AppColors.onSecondaryFixed,
                                        ),
                                        const SizedBox(width: 4),
                                        Text(
                                          'Paste',
                                          style: AppTypography.labelSmall.copyWith(
                                            color: AppColors.onSecondaryFixed,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                IconButton(
                                  icon: const Icon(Icons.close_rounded, size: 18),
                                  color: AppColors.outline,
                                  onPressed: _clearInput,
                                  constraints: const BoxConstraints(),
                                  padding: EdgeInsets.zero,
                                ),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        Row(
                          children: [
                            const Icon(
                              Icons.link_rounded,
                              color: AppColors.primary,
                              size: 24,
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: TextField(
                                controller: _controller,
                                onChanged: (_) => _updateDomain(),
                                style: AppTypography.titleMedium.copyWith(
                                  color: AppColors.onSurface,
                                ),
                                decoration: InputDecoration(
                                  hintText: 'https://example.com/...',
                                  hintStyle: AppTypography.titleMedium.copyWith(
                                    color: AppColors.outline,
                                  ),
                                  border: InputBorder.none,
                                ),
                              ),
                            ),
                          ],
                        ),
                        if (_extractedDomain != null) ...[
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              const Icon(
                                Icons.public_rounded,
                                size: 14,
                                color: AppColors.primaryContainer,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Target Domain: $_extractedDomain',
                                style: AppTypography.bodySmall.copyWith(
                                  color: AppColors.primaryContainer,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),

                  const SizedBox(height: 20),

                  // Quick Examples Card
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
                        Text(
                          'Test Link Examples',
                          style: AppTypography.titleMedium.copyWith(
                            color: AppColors.onSurface,
                          ),
                        ),
                        const SizedBox(height: 10),
                        _LinkExampleRow(
                          label: 'High Risk Phishing URL',
                          url: 'https://sbi-secure-kyc-update.cc/verify',
                          onTap: () {
                            _controller.text =
                                'https://sbi-secure-kyc-update.cc/verify';
                            _updateDomain();
                          },
                        ),
                        const Divider(height: 16),
                        _LinkExampleRow(
                          label: 'Unencrypted Raw IP Address',
                          url: 'http://192.168.1.105/login.html',
                          onTap: () {
                            _controller.text =
                                'http://192.168.1.105/login.html';
                            _updateDomain();
                          },
                        ),
                        const Divider(height: 16),
                        _LinkExampleRow(
                          label: 'Verified Official Portal',
                          url: 'https://www.onlinesbi.sbi',
                          onTap: () {
                            _controller.text = 'https://www.onlinesbi.sbi';
                            _updateDomain();
                          },
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),

                  AppButton(
                    label: 'Analyze Link',
                    icon: Icons.travel_explore_rounded,
                    isLoading: state.isAnalyzing,
                    onPressed: _submitAnalysis,
                  ),

                  const SizedBox(height: 16),
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

class _LinkExampleRow extends StatelessWidget {
  final String label;
  final String url;
  final VoidCallback onTap;

  const _LinkExampleRow({
    required this.label,
    required this.url,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: AppTypography.labelMedium.copyWith(
                    color: AppColors.onSurface,
                  ),
                ),
                Text(
                  url,
                  style: AppTypography.bodySmall.copyWith(
                    color: AppColors.outline,
                  ),
                ),
              ],
            ),
            const Icon(
              Icons.touch_app_rounded,
              size: 16,
              color: AppColors.primary,
            ),
          ],
        ),
      ),
    );
  }
}
