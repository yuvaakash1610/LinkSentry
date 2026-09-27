import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_typography.dart';
import 'article_detail_screen.dart';

class LearnScreen extends StatelessWidget {
  const LearnScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final articles = [
      {
        'title': 'Fake KYC & Bank Block Scams',
        'category': 'Banking Security',
        'icon': Icons.account_balance_rounded,
        'summary':
            'Learn how scammers use panic language like "Account Blocked Today" to steal credentials.',
        'content':
            'Scammers send SMS messages claiming your bank account or SIM card will be suspended within 24 hours unless you update KYC immediately. They include a link to a fake bank website designed to steal your passwords and OTPs.',
        'bullets': [
          'Real banks never ask you to update KYC via third-party SMS links.',
          'Never call the phone number provided inside a suspicious SMS.',
          'Use official bank mobile applications or visit your home branch.',
        ],
      },
      {
        'title': 'OTP & UPI PIN Protection',
        'category': 'Payment Safety',
        'icon': Icons.pin_rounded,
        'summary':
            'Why entering your UPI PIN is ONLY used for sending money, never receiving.',
        'content':
            'A common fraud pattern involves scammers asking you to enter your UPI PIN to "receive a refund" or "collect cashback". Entering your UPI PIN always deducts money from your account.',
        'bullets': [
          'UPI PIN is strictly required to SEND money, never to RECEIVE money.',
          'Never share OTPs over phone calls or WhatsApp messages.',
          'Bank customer care will never demand your secret PIN.',
        ],
      },
      {
        'title': 'Digital Arrest & Video Call Scams',
        'category': 'Threat Awareness',
        'icon': Icons.videocam_off_rounded,
        'summary':
            'Recognize fake law enforcement & police video calls demanding money transfer.',
        'content':
            'Fraudsters impersonate CBI, Police, or Customs officials over video calls, claiming illegal packages were sent in your name and placing you under "digital arrest". They demand immediate money transfers to clear your name.',
        'bullets': [
          'There is no legal concept of "Digital Arrest" over video calls in India.',
          'Police or Customs will never ask you to transfer funds to safe accounts.',
          'Disconnect suspicious video calls immediately and inform CyberCell.',
        ],
      },
      {
        'title': 'Courier & Package Delivery Scams',
        'category': 'Shopping Safety',
        'icon': Icons.local_shipping_rounded,
        'summary':
            'Identify fake IndiaPost, FedEx, or BlueDart delivery failure messages.',
        'content':
            'SMS alerts claim a package cannot be delivered due to an incomplete address and request a nominal ₹5 or ₹10 payment via an untrusted website.',
        'bullets': [
          'Check official tracking numbers directly on official courier apps.',
          'Do not tap shortened tracking links (e.g. bit.ly or .cc domains).',
        ],
      },
      {
        'title': 'Spotting Lookalike & Spoofed URLs',
        'category': 'Link Hygiene',
        'icon': Icons.link_off_rounded,
        'summary':
            'How attackers substitute characters (e.g. sbi-secure-kyc.cc) to trick users.',
        'content':
            'Attackers register domain names that resemble trusted brands by inserting hyphens, extra words, or uncommon extensions (.xyz, .top, .cc).',
        'bullets': [
          'Look closely at the domain name ending right before .com or .in.',
          'Be wary of hyphenated brand names (e.g. hdfc-update-kyc.top).',
          'Ensure the URL starts with https:// and shows a lock icon.',
        ],
      },
    ];

    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        title: const Text('Scam Awareness & Education'),
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
                'Knowledge is your best protection.',
                style: AppTypography.headlineSmall.copyWith(
                  color: AppColors.onSurface,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Understand common mobile fraud vectors and stay one step ahead of scammers.',
                style: AppTypography.bodyMedium.copyWith(
                  color: AppColors.onSurfaceVariant,
                ),
              ),
              const SizedBox(height: 20),

              Column(
                children: articles.map((article) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: _LearnCard(
                      title: article['title'] as String,
                      category: article['category'] as String,
                      summary: article['summary'] as String,
                      icon: article['icon'] as IconData,
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => ArticleDetailScreen(
                              title: article['title'] as String,
                              category: article['category'] as String,
                              icon: article['icon'] as IconData,
                              content: article['content'] as String,
                              bulletPoints: article['bullets'] as List<String>,
                            ),
                          ),
                        );
                      },
                    ),
                  );
                }).toList(),
              ),

              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}

class _LearnCard extends StatelessWidget {
  final String title;
  final String category;
  final String summary;
  final IconData icon;
  final VoidCallback onTap;

  const _LearnCard({
    required this.title,
    required this.category,
    required this.summary,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surfaceContainerLowest,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppColors.surfaceContainerHigh),
            boxShadow: AppColors.cardShadow,
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: AppColors.secondaryContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: AppColors.primary, size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.secondaryFixed,
                        borderRadius: BorderRadius.circular(9999),
                      ),
                      child: Text(
                        category,
                        style: AppTypography.labelSmall.copyWith(
                          color: AppColors.onSecondaryFixed,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      title,
                      style: AppTypography.titleMedium.copyWith(
                        color: AppColors.onSurface,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      summary,
                      style: AppTypography.bodySmall.copyWith(
                        color: AppColors.onSurfaceVariant,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.arrow_forward_ios_rounded,
                size: 16,
                color: AppColors.outline,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
