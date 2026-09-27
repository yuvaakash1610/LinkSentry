enum RiskSeverity { low, medium, high, critical }

class RiskReason {
  final String title;
  final String description;
  final RiskSeverity severity;

  const RiskReason({
    required this.title,
    required this.description,
    this.severity = RiskSeverity.medium,
  });

  Map<String, dynamic> toJson() => {
        'title': title,
        'description': description,
        'severity': severity.name,
      };

  factory RiskReason.fromJson(Map<String, dynamic> json) => RiskReason(
        title: json['title'] as String,
        description: json['description'] as String,
        severity: RiskSeverity.values.firstWhere(
          (e) => e.name == json['severity'],
          orElse: () => RiskSeverity.medium,
        ),
      );
}
