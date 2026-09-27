import 'package:flutter/material.dart';
import '../models/scan_request.dart';
import '../models/scan_result.dart';
import '../models/scan_history_item.dart';
import '../models/live_protection_settings.dart';
import '../models/user_privacy_settings.dart';
import '../services/api_service.dart';
import '../services/storage_service.dart';
import '../services/notification_service.dart';

class AppStateProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  final StorageService _storageService = StorageService();

  int _selectedTabIndex = 0;
  bool _isOnboardingCompleted = false;
  bool _isAnalyzing = false;
  String? _errorMessage;

  ScanResult? _currentResult;
  List<ScanHistoryItem> _history = [];
  LiveProtectionSettings _liveProtection = const LiveProtectionSettings();
  UserPrivacySettings _privacySettings = const UserPrivacySettings();

  // Getters
  int get selectedTabIndex => _selectedTabIndex;
  bool get isOnboardingCompleted => _isOnboardingCompleted;
  bool get isAnalyzing => _isAnalyzing;
  String? get errorMessage => _errorMessage;
  ScanResult? get currentResult => _currentResult;
  List<ScanHistoryItem> get history => _history;
  LiveProtectionSettings get liveProtection => _liveProtection;
  UserPrivacySettings get privacySettings => _privacySettings;

  AppStateProvider() {
    _init();
  }

  Future<void> _init() async {
    _isOnboardingCompleted = await _storageService.isOnboardingCompleted();
    _history = await _storageService.getHistory();
    _liveProtection = await _storageService.getLiveProtectionSettings();
    _privacySettings = await _storageService.getPrivacySettings();

    // Sync notification permission status
    final granted = await NotificationService.isPermissionGranted();
    if (_liveProtection.notificationPermissionGranted != granted) {
      _liveProtection = _liveProtection.copyWith(notificationPermissionGranted: granted);
    }

    notifyListeners();
  }

  void setTabIndex(int index) {
    _selectedTabIndex = index;
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> completeOnboarding() async {
    _isOnboardingCompleted = true;
    await _storageService.setOnboardingCompleted(true);
    notifyListeners();
  }

  /// Analyze Text payload
  Future<ScanResult?> analyzeText(String text, {String? sourceApp}) async {
    if (text.trim().isEmpty) {
      _errorMessage = 'Please enter or paste a message to analyze.';
      notifyListeners();
      return null;
    }

    _isAnalyzing = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final request = ScanRequest(
        id: 'req_${DateTime.now().millisecondsSinceEpoch}',
        type: ScanType.text,
        payload: text,
        sourceApp: sourceApp,
      );

      final result = await _apiService.analyzeText(request);
      _currentResult = result;

      // Add to history summary
      final historyItem = ScanHistoryItem(
        id: result.id,
        scanType: ScanType.text,
        title: text.length > 32 ? '${text.substring(0, 32)}...' : text,
        domain: result.extractedDomain,
        riskScore: result.assessment.score,
        riskLevel: result.assessment.level,
        timestamp: result.analyzedAt,
        payloadPreview: _privacySettings.storeRawMessagesInHistory ? text : null,
      );

      await _storageService.saveHistoryItem(historyItem);
      _history = await _storageService.getHistory();

      _isAnalyzing = false;
      notifyListeners();
      return result;
    } catch (e) {
      _isAnalyzing = false;
      _errorMessage = 'Unable to analyze message right now. Please try again.';
      notifyListeners();
      return null;
    }
  }

  /// Analyze URL payload
  Future<ScanResult?> analyzeUrl(String url) async {
    if (url.trim().isEmpty) {
      _errorMessage = 'Please enter a valid Web URL to analyze.';
      notifyListeners();
      return null;
    }

    _isAnalyzing = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final request = ScanRequest(
        id: 'req_${DateTime.now().millisecondsSinceEpoch}',
        type: ScanType.url,
        payload: url,
      );

      final result = await _apiService.analyzeUrl(request);
      _currentResult = result;

      final historyItem = ScanHistoryItem(
        id: result.id,
        scanType: ScanType.url,
        title: result.extractedDomain ?? url,
        domain: result.extractedDomain,
        riskScore: result.assessment.score,
        riskLevel: result.assessment.level,
        timestamp: result.analyzedAt,
      );

      await _storageService.saveHistoryItem(historyItem);
      _history = await _storageService.getHistory();

      _isAnalyzing = false;
      notifyListeners();
      return result;
    } catch (e) {
      _isAnalyzing = false;
      _errorMessage = 'Unable to analyze link right now. Please try again.';
      notifyListeners();
      return null;
    }
  }

  /// Toggle Live Protection state
  Future<void> toggleLiveProtection(bool enabled) async {
    _liveProtection = _liveProtection.copyWith(isEnabled: enabled);
    await _storageService.saveLiveProtectionSettings(_liveProtection);
    await NotificationService.setLiveProtectionEnabled(enabled);
    notifyListeners();
  }

  /// Toggle monitored apps for Live Protection
  Future<void> toggleMonitoredApp(String appName) async {
    final updated = List<String>.from(_liveProtection.monitoredApps);
    if (updated.contains(appName)) {
      updated.remove(appName);
    } else {
      updated.add(appName);
    }
    _liveProtection = _liveProtection.copyWith(monitoredApps: updated);
    await _storageService.saveLiveProtectionSettings(_liveProtection);
    notifyListeners();
  }

  /// Request Notification Permission
  Future<void> requestNotificationPermission() async {
    await NotificationService.requestPermission();
    final granted = await NotificationService.isPermissionGranted();
    _liveProtection = _liveProtection.copyWith(notificationPermissionGranted: granted);
    await _storageService.saveLiveProtectionSettings(_liveProtection);
    notifyListeners();
  }

  /// Delete specific history item
  Future<void> deleteHistoryItem(String id) async {
    await _storageService.deleteHistoryItem(id);
    _history = await _storageService.getHistory();
    notifyListeners();
  }

  /// Clear all history items
  Future<void> clearAllHistory() async {
    await _storageService.clearHistory();
    _history = [];
    notifyListeners();
  }

  /// Save Privacy settings
  Future<void> updatePrivacySettings(UserPrivacySettings settings) async {
    _privacySettings = settings;
    await _storageService.savePrivacySettings(settings);
    notifyListeners();
  }

  /// Clear current result & error
  void clearResult() {
    _currentResult = null;
    _errorMessage = null;
    notifyListeners();
  }
}
