import '../../models/risk_assessment.dart';
import '../../models/risk_reason.dart';
import 'url_extractor.dart';

class RiskCalculator {
  RiskCalculator._();

  static RiskAssessment analyzeText(String text) {
    if (text.trim().isEmpty) {
      return RiskAssessment.create(
        score: 0,
        summary: 'No text provided to analyze.',
        reasons: [],
        recommendedActions: ['Enter or paste message content to analyze.'],
      );
    }

    int score = 10; // baseline score
    final reasons = <RiskReason>[];
    final actions = <String>[];

    final lower = text.toLowerCase();
    final urls = UrlExtractor.extractUrls(text);

    // Heuristic 1: Urgency & Blocking Language
    if (lower.contains('block') ||
        lower.contains('suspend') ||
        lower.contains('within 24 hours') ||
        lower.contains('immediately') ||
        lower.contains('urgent') ||
        lower.contains('today')) {
      score += 25;
      reasons.add(const RiskReason(
        title: 'Urgent account-blocking language',
        description:
            'The message uses artificial time pressure or threat of suspension to force immediate action.',
        severity: RiskSeverity.high,
      ));
    }

    // Heuristic 2: Sensitive Info / KYC requests
    if (lower.contains('kyc') ||
        lower.contains('verify identity') ||
        lower.contains('otp') ||
        lower.contains('pin') ||
        lower.contains('cvv') ||
        lower.contains('bank account')) {
      score += 30;
      reasons.add(const RiskReason(
        title: 'Requests sensitive information or KYC',
        description:
            'Message asks for credentials, OTPs, or identity verification through non-official channels.',
        severity: RiskSeverity.critical,
      ));
    }

    // Heuristic 3: Suspicious URL in text
    if (urls.isNotEmpty) {
      for (final url in urls) {
        final domain = UrlExtractor.extractDomain(url) ?? '';
        if (domain.contains('-kyc') ||
            domain.contains('secure') ||
            domain.contains('login') ||
            domain.endsWith('.cc') ||
            domain.endsWith('.xyz') ||
            domain.endsWith('.top') ||
            domain.endsWith('.info') ||
            domain.endsWith('.click') ||
            RegExp(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}').hasMatch(domain)) {
          score += 30;
          reasons.add(RiskReason(
            title: 'Suspicious domain structure ($domain)',
            description:
                'The domain uses spoofed keywords or suspicious top-level extensions commonly associated with phishing.',
            severity: RiskSeverity.critical,
          ));
          break;
        } else {
          score += 15;
          reasons.add(RiskReason(
            title: 'Contains unverified link ($domain)',
            description:
                'Always verify link targets independently before clicking.',
            severity: RiskSeverity.medium,
          ));
        }
      }
    }

    // Cap score at 100
    if (score > 100) score = 100;

    // Recommended Actions based on score
    if (score >= 60) {
      actions.addAll([
        'Do not open the link',
        'Do not share OTP, PIN, or CVV',
        'Do not share UPI PIN or password',
        'Open the official bank/service app directly',
        'Manually type official website URL in your browser',
      ]);
    } else if (score >= 30) {
      actions.addAll([
        'Verify the sender through an official phone number or website',
        'Do not tap links in unrequested SMS messages',
        'Check official application for alert notifications',
      ]);
    } else {
      actions.addAll([
        'Message appears low risk based on standard heuristics.',
        'Remain vigilant when sharing sensitive personal data.',
      ]);
    }

    String summary;
    if (score >= 80) {
      summary =
          'This message exhibits multiple high-risk indicators typical of fraudulent phishing and KYC scams.';
    } else if (score >= 60) {
      summary =
          'Potential phishing attempt detected. Exercise caution and do not follow embedded instructions.';
    } else if (score >= 30) {
      summary =
          'Unverified message details detected. Verify independently before acting.';
    } else {
      summary =
          'No immediate threat patterns detected. Content appears low risk.';
    }

    return RiskAssessment.create(
      score: score,
      summary: summary,
      reasons: reasons.isEmpty
          ? [
              const RiskReason(
                title: 'No malicious patterns detected',
                description:
                    'Message structure matches standard notification formats without urgent threats.',
                severity: RiskSeverity.low,
              )
            ]
          : reasons,
      recommendedActions: actions,
    );
  }

  static RiskAssessment analyzeUrl(String url) {
    if (url.trim().isEmpty) {
      return RiskAssessment.create(
        score: 0,
        summary: 'No URL provided to analyze.',
        reasons: [],
        recommendedActions: ['Enter or paste a valid web address.'],
      );
    }

    final domain = UrlExtractor.extractDomain(url) ?? url;
    int score = 15;
    final reasons = <RiskReason>[];
    final actions = <String>[];

    final lowerDomain = domain.toLowerCase();
    final lowerUrl = url.toLowerCase();

    // Check for IP address URL
    if (RegExp(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}').hasMatch(domain)) {
      score += 45;
      reasons.add(const RiskReason(
        title: 'Raw IP address used as hostname',
        description:
            'Legitimate services almost never use raw IP addresses for consumer links.',
        severity: RiskSeverity.critical,
      ));
    }

    // Check for suspicious TLDs
    if (lowerDomain.endsWith('.cc') ||
        lowerDomain.endsWith('.xyz') ||
        lowerDomain.endsWith('.top') ||
        lowerDomain.endsWith('.click') ||
        lowerDomain.endsWith('.work') ||
        lowerDomain.endsWith('.info')) {
      score += 35;
      reasons.add(RiskReason(
        title: 'High-risk top-level domain ($domain)',
        description:
            'This domain extension is frequently associated with disposable phishing campaigns.',
        severity: RiskSeverity.high,
      ));
    }

    // Check for spoofing hyphenated brand combinations
    if (lowerDomain.contains('sbi-') ||
        lowerDomain.contains('hdfc-') ||
        lowerDomain.contains('icici-') ||
        lowerDomain.contains('amazon-') ||
        lowerDomain.contains('kyc-') ||
        lowerDomain.contains('-update') ||
        lowerDomain.contains('-verify')) {
      score += 40;
      reasons.add(const RiskReason(
        title: 'Brand impersonation keyword pattern',
        description:
            'Domain name combines trusted brand names with suspicious verification suffixes.',
        severity: RiskSeverity.critical,
      ));
    }

    // Check HTTP vs HTTPS
    if (lowerUrl.startsWith('http://')) {
      score += 20;
      reasons.add(const RiskReason(
        title: 'Unencrypted HTTP connection',
        description:
            'This link does not use SSL encryption (HTTPS), leaving transmitted data vulnerable.',
        severity: RiskSeverity.medium,
      ));
    }

    if (score > 100) score = 100;

    if (score >= 60) {
      actions.addAll([
        'Do not open this URL in your web browser',
        'Do not enter credentials or bank account details',
        'Use official mobile app or type the verified domain manually',
      ]);
    } else if (score >= 30) {
      actions.addAll([
        'Double check domain spelling before entering login details',
        'Ensure lock icon is visible in browser bar',
      ]);
    } else {
      actions.addAll([
        'Domain structure appears standard.',
        'Always double-check website address bar after page loads.',
      ]);
    }

    return RiskAssessment.create(
      score: score,
      summary: score >= 60
          ? 'Potentially unsafe destination link. High probability of credential harvesting or fraud.'
          : score >= 30
              ? 'Unverified domain structure. Exercise care when interacting.'
              : 'Destination domain appears low risk.',
      reasons: reasons.isEmpty
          ? [
              const RiskReason(
                title: 'Standard domain structure',
                description: 'No known phishing patterns found for this domain.',
                severity: RiskSeverity.low,
              )
            ]
          : reasons,
      recommendedActions: actions,
    );
  }
}
