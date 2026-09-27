import 'risk_reason.dart';

enum RiskLevel {
  lowRisk,
  verifyIndependently,
  suspicious,
  highRisk,
}

extension RiskLevelExtension on RiskLevel {
  String get label {
    switch (this) {
      case RiskLevel.lowRisk:
        return 'Low Risk';
      case RiskLevel.verifyIndependently:
        return 'Verify Independently';
      case RiskLevel.suspicious:
        return 'Suspicious';
      case RiskLevel.highRisk:
        return 'High Risk';
    }
  }

  static RiskLevel fromScore(int score) {
    if (score < 30) return RiskLevel.lowRisk;
    if (score < 60) return RiskLevel.verifyIndependently;
    if (score < 80) return RiskLevel.suspicious;
    return RiskLevel.highRisk;
  }
}

class RiskAssessment {
  final int score; // 0 to 100
  final RiskLevel level;
  final String summary;
  final List<RiskReason> reasons;
  final List<String> recommendedActions;

  const RiskAssessment({
    required this.score,
    required this.level,
    required this.summary,
    required this.reasons,
    required this.recommendedActions,
  });

  factory RiskAssessment.create({
    required int score,
    required String summary,
    required List<RiskReason> reasons,
    required List<String> recommendedActions,
  }) {
    return RiskAssessment(
      score: score,
      level: RiskLevelExtension.fromScore(score),
      summary: summary,
      reasons: reasons,
      recommendedActions: recommendedActions,
    );
  }

  Map<String, dynamic> toJson() => {
        'score': score,
        'level': level.name,
        'summary': summary,
        'reasons': reasons.map((r) => r.toJson()).toList(),
        'recommendedActions': recommendedActions,
      };

  factory RiskAssessment.fromJson(Map<String, dynamic> json) => RiskAssessment(
        score: json['score'] as int,
        level: RiskLevel.values.firstWhere(
          (e) => e.name == json['level'],
          orElse: () => RiskLevelExtension.fromScore(json['score'] as int),
        ),
        summary: json['summary'] as String,
        reasons: (json['reasons'] as List)
            .map((r) => RiskReason.fromJson(r as Map<String, dynamic>))
            .toList(),
        recommendedActions: List<String>.from(json['recommendedActions'] as List),
      );
}
