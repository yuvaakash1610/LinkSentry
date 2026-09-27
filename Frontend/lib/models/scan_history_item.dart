import 'risk_assessment.dart';
import 'scan_request.dart';

class ScanHistoryItem {
  final String id;
  final ScanType scanType;
  final String title;
  final String? domain;
  final int riskScore;
  final RiskLevel riskLevel;
  final DateTime timestamp;
  final String? payloadPreview;

  ScanHistoryItem({
    required this.id,
    required this.scanType,
    required this.title,
    this.domain,
    required this.riskScore,
    required this.riskLevel,
    required this.timestamp,
    this.payloadPreview,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'scanType': scanType.name,
        'title': title,
        'domain': domain,
        'riskScore': riskScore,
        'riskLevel': riskLevel.name,
        'timestamp': timestamp.toIso8601String(),
        'payloadPreview': payloadPreview,
      };

  factory ScanHistoryItem.fromJson(Map<String, dynamic> json) => ScanHistoryItem(
        id: json['id'] as String,
        scanType: ScanType.values.firstWhere((e) => e.name == json['scanType']),
        title: json['title'] as String,
        domain: json['domain'] as String?,
        riskScore: json['riskScore'] as int,
        riskLevel: RiskLevel.values.firstWhere(
          (e) => e.name == json['riskLevel'],
          orElse: () => RiskLevelExtension.fromScore(json['riskScore'] as int),
        ),
        timestamp: DateTime.parse(json['timestamp'] as String),
        payloadPreview: json['payloadPreview'] as String?,
      );
}
