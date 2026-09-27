import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/scan_option_card.dart';
import '../../core/widgets/privacy_disclaimer_card.dart';
import 'text_scan_screen.dart';
import 'url_scan_screen.dart';
import 'qr_scan_screen.dart';

class ScanHubScreen extends StatelessWidget {
  const ScanHubScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        title: const Text('Scan & Verify Hub'),
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
                'Select Protection Vector',
                style: AppTypography.headlineSmall.copyWith(
                  color: AppColors.onSurface,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Choose how you want to inspect suspicious content before taking action.',
                style: AppTypography.bodyMedium.copyWith(
                  color: AppColors.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 20),

              ScanOptionCard(
                title: 'Message & Text Scan',
                description:
                    'Paste SMS text, copied emails, or WhatsApp alerts to check for urgency & KYC fraud patterns.',
                icon: Icons.sms_outlined,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const TextScanScreen(),
                    ),
                  );
                },
              ),
              const SizedBox(height: 14),

              ScanOptionCard(
                title: 'URL & Link Inspection',
                description:
                    'Analyze web addresses, shortened links, or suspicious domains before opening them in a browser.',
                icon: Icons.link_rounded,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const UrlScanScreen(),
                    ),
                  );
                },
              ),
              const SizedBox(height: 14),

              ScanOptionCard(
                title: 'QR Code Destination Scanner',
                description:
                    'Use camera to read QR code destination URLs securely without automatic redirection.',
                icon: Icons.qr_code_scanner_rounded,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const QrScanScreen(),
                    ),
                  );
                },
              ),

              const SizedBox(height: 24),
              const PrivacyDisclaimerCard(),
            ],
          ),
        ),
      ),
    );
  }
}
