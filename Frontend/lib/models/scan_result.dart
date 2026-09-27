import 'scan_request.dart';
import 'risk_assessment.dart';

class ScanResult {
  final String id;
  final ScanRequest request;
  final RiskAssessment assessment;
  final String? extractedDomain;
  final List<String> extractedUrls;
  final DateTime analyzedAt;
  final bool isMockData;

  ScanResult({
    required this.id,
    required this.request,
    required this.assessment,
    this.extractedDomain,
    this.extractedUrls = const [],
    DateTime? analyzedAt,
    this.isMockData = true,
  }) : analyzedAt = analyzedAt ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'id': id,
        'request': request.toJson(),
        'assessment': assessment.toJson(),
        'extractedDomain': extractedDomain,
        'extractedUrls': extractedUrls,
        'analyzedAt': analyzedAt.toIso8601String(),
        'isMockData': isMockData,
      };

  factory ScanResult.fromJson(Map<String, dynamic> json) => ScanResult(
        id: json['id'] as String,
        request: ScanRequest.fromJson(json['request'] as Map<String, dynamic>),
        assessment:
            RiskAssessment.fromJson(json['assessment'] as Map<String, dynamic>),
        extractedDomain: json['extractedDomain'] as String?,
        extractedUrls: List<String>.from(json['extractedUrls'] ?? []),
        analyzedAt: DateTime.parse(json['analyzedAt'] as String),
        isMockData: json['isMockData'] as bool? ?? false,
      );
}
