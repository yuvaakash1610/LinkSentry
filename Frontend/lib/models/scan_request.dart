enum ScanType { text, url, qr, notification }

class ScanRequest {
  final String id;
  final ScanType type;
  final String payload;
  final DateTime timestamp;
  final String? sourceApp;

  ScanRequest({
    required this.id,
    required this.type,
    required this.payload,
    DateTime? timestamp,
    this.sourceApp,
  }) : timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type.name,
        'payload': payload,
        'timestamp': timestamp.toIso8601String(),
        'sourceApp': sourceApp,
      };

  factory ScanRequest.fromJson(Map<String, dynamic> json) => ScanRequest(
        id: json['id'] as String,
        type: ScanType.values.firstWhere((e) => e.name == json['type']),
        payload: json['payload'] as String,
        timestamp: DateTime.parse(json['timestamp'] as String),
        sourceApp: json['sourceApp'] as String?,
      );
}
