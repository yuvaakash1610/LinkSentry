import 'package:flutter/services.dart';

class NotificationService {
  static const MethodChannel _channel =
      MethodChannel('com.linksentry.app/notification_listener');

  /// Check if Android Notification Access permission is granted
  static Future<bool> isPermissionGranted() async {
    try {
      final bool granted = await _channel.invokeMethod('isPermissionGranted');
      return granted;
    } on PlatformException catch (_) {
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Open Android Notification Access settings screen
  static Future<void> requestPermission() async {
    try {
      await _channel.invokeMethod('requestPermission');
    } on PlatformException catch (_) {
      // Fallback or ignore on non-Android platforms
    }
  }

  /// Enable or disable background listener service
  static Future<bool> setLiveProtectionEnabled(bool enabled) async {
    try {
      final bool success =
          await _channel.invokeMethod('setLiveProtectionEnabled', {'enabled': enabled});
      return success;
    } catch (_) {
      return enabled;
    }
  }
}
