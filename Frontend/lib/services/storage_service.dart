import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/scan_history_item.dart';
import '../models/live_protection_settings.dart';
import '../models/user_privacy_settings.dart';

class StorageService {
  static const String _keyHistory = 'linksentry_scan_history';
  static const String _keyLiveProtection = 'linksentry_live_protection';
  static const String _keyPrivacy = 'linksentry_privacy_settings';
  static const String _keyOnboardingDone = 'linksentry_onboarding_completed';

  Future<SharedPreferences> get _prefs => SharedPreferences.getInstance();

  /// Save onboarding completed flag
  Future<void> setOnboardingCompleted(bool value) async {
    final prefs = await _prefs;
    await prefs.setBool(_keyOnboardingDone, value);
  }

  /// Get onboarding completed flag
  Future<bool> isOnboardingCompleted() async {
    final prefs = await _prefs;
    return prefs.getBool(_keyOnboardingDone) ?? false;
  }

  /// Save scan result to local history
  Future<void> saveHistoryItem(ScanHistoryItem item) async {
    final history = await getHistory();
    // Add to top of list
    history.insert(0, item);
    // Limit history length to 50 items
    if (history.length > 50) history.removeLast();

    final prefs = await _prefs;
    final jsonList = history.map((e) => e.toJson()).toList();
    await prefs.setString(_keyHistory, jsonEncode(jsonList));
  }

  /// Get all history items
  Future<List<ScanHistoryItem>> getHistory() async {
    final prefs = await _prefs;
    final jsonStr = prefs.getString(_keyHistory);
    if (jsonStr == null || jsonStr.isEmpty) return [];

    try {
      final List decoded = jsonDecode(jsonStr) as List;
      return decoded
          .map((e) => ScanHistoryItem.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  /// Delete specific history item by ID
  Future<void> deleteHistoryItem(String id) async {
    final history = await getHistory();
    history.removeWhere((item) => item.id == id);
    final prefs = await _prefs;
    final jsonList = history.map((e) => e.toJson()).toList();
    await prefs.setString(_keyHistory, jsonEncode(jsonList));
  }

  /// Clear all history
  Future<void> clearHistory() async {
    final prefs = await _prefs;
    await prefs.remove(_keyHistory);
  }

  /// Save Live Protection settings
  Future<void> saveLiveProtectionSettings(LiveProtectionSettings settings) async {
    final prefs = await _prefs;
    await prefs.setString(_keyLiveProtection, jsonEncode(settings.toJson()));
  }

  /// Load Live Protection settings
  Future<LiveProtectionSettings> getLiveProtectionSettings() async {
    final prefs = await _prefs;
    final jsonStr = prefs.getString(_keyLiveProtection);
    if (jsonStr == null) return const LiveProtectionSettings();
    try {
      return LiveProtectionSettings.fromJson(
          jsonDecode(jsonStr) as Map<String, dynamic>);
    } catch (_) {
      return const LiveProtectionSettings();
    }
  }

  /// Save User Privacy settings
  Future<void> savePrivacySettings(UserPrivacySettings settings) async {
    final prefs = await _prefs;
    await prefs.setString(_keyPrivacy, jsonEncode(settings.toJson()));
  }

  /// Load User Privacy settings
  Future<UserPrivacySettings> getPrivacySettings() async {
    final prefs = await _prefs;
    final jsonStr = prefs.getString(_keyPrivacy);
    if (jsonStr == null) return const UserPrivacySettings();
    try {
      return UserPrivacySettings.fromJson(
          jsonDecode(jsonStr) as Map<String, dynamic>);
    } catch (_) {
      return const UserPrivacySettings();
    }
  }
}
