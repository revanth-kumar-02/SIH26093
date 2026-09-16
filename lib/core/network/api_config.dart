import 'package:flutter/foundation.dart';

/// Central API Configuration for SIH26093.
///
/// Supports Web, Android Emulator (10.0.2.2), and physical Android device over LAN.
class ApiConfig {
  ApiConfig._();

  /// Default LAN IP for physical device testing on local Wi-Fi.
  static const String defaultLanIp = '172.16.104.30';

  /// Compile-time environment override via `--dart-define=API_BASE_URL=...`
  static const String _envBaseUrl = String.fromEnvironment('API_BASE_URL');

  /// Runtime override if changed dynamically during testing.
  static String? customBaseUrl;

  /// Resolves the appropriate base URL for the active platform.
  static String get baseUrl {
    if (customBaseUrl != null && customBaseUrl!.isNotEmpty) {
      return customBaseUrl!;
    }
    if (_envBaseUrl.isNotEmpty) {
      return _envBaseUrl;
    }

    if (kIsWeb) {
      return 'http://127.0.0.1:8000';
    }

    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return 'http://$defaultLanIp:8000';
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
      case TargetPlatform.windows:
      case TargetPlatform.linux:
      case TargetPlatform.fuchsia:
        return 'http://127.0.0.1:8000';
    }
  }

  /// Standard request timeout to prevent hanging UI.
  static const Duration timeoutDuration = Duration(seconds: 8);

  // --- Victim Endpoint paths ---
  static String get healthUrl => '$baseUrl/health';
  static String get sessionsUrl => '$baseUrl/api/v1/sessions';
  static String sessionMessagesUrl(String sessionId) => '$baseUrl/api/v1/sessions/$sessionId/messages';
  static String sessionAssessmentUrl(String sessionId) => '$baseUrl/api/v1/sessions/$sessionId/assessment';
  static String sessionTranscribeUrl(String sessionId) => '$baseUrl/api/v1/sessions/$sessionId/transcribe';
  static String sessionAnalyzeTextUrl(String sessionId) => '$baseUrl/api/v1/sessions/$sessionId/analyze/text';
  static String sessionAnalyzeAudioUrl(String sessionId) => '$baseUrl/api/v1/sessions/$sessionId/analyze/audio';

  // --- Admin Endpoint paths (Phase 11) ---
  static String get adminDashboardUrl => '$baseUrl/api/v1/admin/dashboard';
  static String get adminCasesUrl => '$baseUrl/api/v1/admin/cases';
  static String adminCaseDetailUrl(String caseId) => '$baseUrl/api/v1/admin/cases/$caseId';
  static String get adminAuditUrl => '$baseUrl/api/v1/admin/audit';
  static String adminCaseStatusUrl(String caseId) => '$baseUrl/api/v1/admin/cases/$caseId/status';
  static String adminReviewRecommendationUrl(String recId) =>
      '$baseUrl/api/v1/admin/recommendations/$recId/review';

  // --- Responder & Auth Endpoint paths (Phase 9) ---
  static String get authLoginUrl => '$baseUrl/api/v1/auth/login';
  static String get authRefreshUrl => '$baseUrl/api/v1/auth/refresh';
  static String get authMeUrl => '$baseUrl/api/v1/auth/me';
  static String get responderCasesUrl => '$baseUrl/api/v1/responder/cases';
  static String responderCaseDetailUrl(String caseId) => '$baseUrl/api/v1/responder/cases/$caseId';
  static String responderCaseAssignUrl(String caseId) => '$baseUrl/api/v1/responder/cases/$caseId/assign';
  static String responderCaseStatusUrl(String caseId) => '$baseUrl/api/v1/responder/cases/$caseId/status';
  static String responderReviewRecommendationUrl(String caseId, String recId) =>
      '$baseUrl/api/v1/responder/cases/$caseId/recommendations/$recId/review';
  static String responderCaseAuditUrl(String caseId) => '$baseUrl/api/v1/responder/cases/$caseId/audit';
}
