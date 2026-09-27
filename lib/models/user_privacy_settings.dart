class UserPrivacySettings {
  final bool storeRawMessagesInHistory;
  final bool localAnalysisOnly;
  final bool anonymousTelemetry;

  const UserPrivacySettings({
    this.storeRawMessagesInHistory = false,
    this.localAnalysisOnly = true,
    this.anonymousTelemetry = false,
  });

  UserPrivacySettings copyWith({
    bool? storeRawMessagesInHistory,
    bool? localAnalysisOnly,
    bool? anonymousTelemetry,
  }) {
    return UserPrivacySettings(
      storeRawMessagesInHistory:
          storeRawMessagesInHistory ?? this.storeRawMessagesInHistory,
      localAnalysisOnly: localAnalysisOnly ?? this.localAnalysisOnly,
      anonymousTelemetry: anonymousTelemetry ?? this.anonymousTelemetry,
    );
  }

  Map<String, dynamic> toJson() => {
        'storeRawMessagesInHistory': storeRawMessagesInHistory,
        'localAnalysisOnly': localAnalysisOnly,
        'anonymousTelemetry': anonymousTelemetry,
      };

  factory UserPrivacySettings.fromJson(Map<String, dynamic> json) =>
      UserPrivacySettings(
        storeRawMessagesInHistory:
            json['storeRawMessagesInHistory'] as bool? ?? false,
        localAnalysisOnly: json['localAnalysisOnly'] as bool? ?? true,
        anonymousTelemetry: json['anonymousTelemetry'] as bool? ?? false,
      );
}
