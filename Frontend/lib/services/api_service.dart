import 'dart:async';
import '../models/scan_request.dart';
import '../models/scan_result.dart';
import '../core/utils/risk_calculator.dart';
import '../core/utils/url_extractor.dart';

class ApiService {
  final String baseUrl;
  final bool useMockData;

  ApiService({
    this.baseUrl = 'https://api.linksentry.app',
    this.useMockData = true,
  });

  /// Analyze text message payload
  Future<ScanResult> analyzeText(ScanRequest request) async {
    if (useMockData) {
      // Simulate realistic network analysis latency (600ms - 1.2s)
      await Future.delayed(const Duration(milliseconds: 900));

      final text = request.payload;
      final extractedUrls = UrlExtractor.extractUrls(text);
      final domain = extractedUrls.isNotEmpty
          ? UrlExtractor.extractDomain(extractedUrls.first)
          : null;

      final assessment = RiskCalculator.analyzeText(text);

      return ScanResult(
        id: 'res_${DateTime.now().millisecondsSinceEpoch}',
        request: request,
        assessment: assessment,
        extractedDomain: domain,
        extractedUrls: extractedUrls,
        isMockData: true,
      );
    } else {
      // Endpoint: POST /api/analyze/text
      // Implementation ready for real FastAPI integration
      throw UnimplementedError('Backend API integration ready. Enable server config.');
    }
  }

  /// Analyze URL destination
  Future<ScanResult> analyzeUrl(ScanRequest request) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 800));

      final url = request.payload;
      final domain = UrlExtractor.extractDomain(url) ?? url;
      final assessment = RiskCalculator.analyzeUrl(url);

      return ScanResult(
        id: 'res_${DateTime.now().millisecondsSinceEpoch}',
        request: request,
        assessment: assessment,
        extractedDomain: domain,
        extractedUrls: [url],
        isMockData: true,
      );
    } else {
      // Endpoint: POST /api/analyze/url
      throw UnimplementedError('Backend API integration ready.');
    }
  }

  /// Send feedback for a scan result
  Future<bool> sendFeedback({
    required String scanId,
    required bool isAccurate,
    String? userComments,
  }) async {
    if (useMockData) {
      await Future.delayed(const Duration(milliseconds: 400));
      return true;
    } else {
      // Endpoint: POST /api/feedback
      return true;
    }
  }

  /// Check API backend health status
  Future<bool> checkHealth() async {
    if (useMockData) return true;
    // Endpoint: GET /api/health
    return true;
  }
}
