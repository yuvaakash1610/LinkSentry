class LiveProtectionSettings {
  final bool isEnabled;
  final bool notificationPermissionGranted;
  final List<String> monitoredApps;
  final bool notifyOnSuspiciousOnly;

  const LiveProtectionSettings({
    this.isEnabled = false,
    this.notificationPermissionGranted = false,
    this.monitoredApps = const ['Messages', 'WhatsApp', 'Telegram', 'Email'],
    this.notifyOnSuspiciousOnly = true,
  });

  LiveProtectionSettings copyWith({
    bool? isEnabled,
    bool? notificationPermissionGranted,
    List<String>? monitoredApps,
    bool? notifyOnSuspiciousOnly,
  }) {
    return LiveProtectionSettings(
      isEnabled: isEnabled ?? this.isEnabled,
      notificationPermissionGranted:
          notificationPermissionGranted ?? this.notificationPermissionGranted,
      monitoredApps: monitoredApps ?? this.monitoredApps,
      notifyOnSuspiciousOnly:
          notifyOnSuspiciousOnly ?? this.notifyOnSuspiciousOnly,
    );
  }

  Map<String, dynamic> toJson() => {
        'isEnabled': isEnabled,
        'notificationPermissionGranted': notificationPermissionGranted,
        'monitoredApps': monitoredApps,
        'notifyOnSuspiciousOnly': notifyOnSuspiciousOnly,
      };

  factory LiveProtectionSettings.fromJson(Map<String, dynamic> json) =>
      LiveProtectionSettings(
        isEnabled: json['isEnabled'] as bool? ?? false,
        notificationPermissionGranted:
            json['notificationPermissionGranted'] as bool? ?? false,
        monitoredApps: List<String>.from(
            json['monitoredApps'] ?? ['Messages', 'WhatsApp', 'Telegram', 'Email']),
        notifyOnSuspiciousOnly: json['notifyOnSuspiciousOnly'] as bool? ?? true,
      );
}
