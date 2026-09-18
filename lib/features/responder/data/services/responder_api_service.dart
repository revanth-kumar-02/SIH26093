import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../../../core/network/api_config.dart';
import '../../../../core/network/api_exceptions.dart';
import '../models/responder_models.dart';

import '../../../../core/services/supabase_auth_service.dart';

class ResponderApiException extends ApiException {
  final int? statusCode;
  const ResponderApiException(String message, {this.statusCode})
      : super(userMessage: message);
}

/// Service managing responder authentication, authorization tokens, and API communication.
class ResponderApiService {
  ResponderApiService._();
  static final ResponderApiService instance = ResponderApiService._();

  ResponderAuthSession? _session;
  ResponderAuthSession? get session => _session;
  String? get activeToken => _session?.accessToken ?? SupabaseAuthService.instance.accessToken;
  bool get isAuthenticated => (_session != null && _session!.accessToken.isNotEmpty) || SupabaseAuthService.instance.isAdmin;

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        if (activeToken != null && activeToken!.isNotEmpty) 'Authorization': 'Bearer $activeToken',
      };

  /// Authenticate responder with credentials
  Future<ResponderAuthSession> login(String username, String password) async {
    try {
      final response = await http
          .post(
            Uri.parse(ApiConfig.authLoginUrl),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'username': username.trim(),
              'password': password,
            }),
          )
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _session = ResponderAuthSession.fromJson(data);
        return _session!;
      } else {
        final err = jsonDecode(response.body);
        final msg = err['error']?['message'] ?? 'Authentication failed.';
        throw ResponderApiException(msg.toString(), statusCode: response.statusCode);
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Unable to reach server. Please check your network connection.');
    }
  }

  /// Invalidate local session
  void logout() {
    _session = null;
  }

  /// List cases with optional filters
  Future<List<CaseListItemModel>> fetchCases({
    int page = 1,
    int pageSize = 20,
    String? status,
    String? riskCategory,
    bool assignedToMe = false,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{
        'page': page.toString(),
        'page_size': pageSize.toString(),
        if (status != null && status.isNotEmpty) 'case_status': status,
        if (riskCategory != null && riskCategory.isNotEmpty) 'risk_category': riskCategory,
        if (assignedToMe) 'assigned_to_me': 'true',
        if (search != null && search.isNotEmpty) 'search': search,
      };

      final uri = Uri.parse(ApiConfig.responderCasesUrl).replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: _headers).timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final items = data['items'] as List<dynamic>? ?? [];
        return items.map((e) => CaseListItemModel.fromJson(e as Map<String, dynamic>)).toList();
      } else if (response.statusCode == 401) {
        logout();
        throw const ResponderApiException('Session expired. Please log in again.', statusCode: 401);
      } else {
        throw ServerErrorException(statusCode: response.statusCode, userMessage: 'Failed to retrieve cases (${response.statusCode}).');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while retrieving cases.');
    }
  }

  /// Fetch full case details
  Future<CaseDetailModel> fetchCaseDetail(String caseId) async {
    try {
      final uri = Uri.parse(ApiConfig.responderCaseDetailUrl(caseId));
      final response = await http.get(uri, headers: _headers).timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return CaseDetailModel.fromJson(data);
      } else if (response.statusCode == 401) {
        logout();
        throw const ResponderApiException('Session expired. Please log in again.', statusCode: 401);
      } else if (response.statusCode == 403) {
        throw const ResponderApiException('You are not authorized to view this assigned case.', statusCode: 403);
      } else {
        throw ServerErrorException(statusCode: response.statusCode, userMessage: 'Failed to retrieve case details.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while retrieving case details.');
    }
  }

  /// Assign case to responder (Supervisor/Admin)
  Future<void> assignCase(String caseId, String responderId) async {
    try {
      final uri = Uri.parse(ApiConfig.responderCaseAssignUrl(caseId));
      final response = await http
          .post(
            uri,
            headers: _headers,
            body: jsonEncode({'responder_id': responderId}),
          )
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body);
        throw ResponderApiException(err['error']?['message']?.toString() ?? 'Failed to assign case.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while assigning case.');
    }
  }

  /// Update case lifecycle status
  Future<void> updateCaseStatus(String caseId, String newStatus) async {
    try {
      final uri = Uri.parse(ApiConfig.responderCaseStatusUrl(caseId));
      final response = await http
          .post(
            uri,
            headers: _headers,
            body: jsonEncode({'status': newStatus}),
          )
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body);
        throw ResponderApiException(err['error']?['message']?.toString() ?? 'Failed to update status.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while updating status.');
    }
  }

  /// Human decision on AI recommendation
  Future<void> reviewRecommendation(
    String caseId,
    String recId,
    String decision, {
    String? modifiedAction,
    String? note,
  }) async {
    try {
      final uri = Uri.parse(ApiConfig.responderReviewRecommendationUrl(caseId, recId));
      final response = await http
          .post(
            uri,
            headers: _headers,
            body: jsonEncode({
              'decision': decision,
              if (modifiedAction != null && modifiedAction.isNotEmpty) 'modified_action': modifiedAction,
              if (note != null && note.isNotEmpty) 'responder_note': note,
            }),
          )
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body);
        throw ResponderApiException(err['error']?['message']?.toString() ?? 'Failed to record decision.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while recording decision.');
    }
  }

  /// Retrieve append-only audit trail
  Future<List<AuditEventModel>> fetchAuditTrail(String caseId) async {
    try {
      final uri = Uri.parse(ApiConfig.responderCaseAuditUrl(caseId));
      final response = await http.get(uri, headers: _headers).timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List<dynamic>;
        return data.map((e) => AuditEventModel.fromJson(e as Map<String, dynamic>)).toList();
      } else {
        throw ServerErrorException(statusCode: response.statusCode, userMessage: 'Failed to retrieve audit trail.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while retrieving audit trail.');
    }
  }

  /// Fetch live structured aggregates for Admin Dashboard
  Future<DashboardAnalyticsModel> fetchAdminDashboard() async {
    try {
      final response = await http
          .get(Uri.parse(ApiConfig.adminDashboardUrl), headers: _headers)
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return DashboardAnalyticsModel.fromJson(data);
      } else if (response.statusCode == 401) {
        logout();
        throw const ResponderApiException('Session expired. Please log in again.', statusCode: 401);
      } else if (response.statusCode == 403) {
        throw const ResponderApiException('Access denied. Administrator privileges required.', statusCode: 403);
      } else {
        throw ServerErrorException(statusCode: response.statusCode, userMessage: 'Failed to retrieve admin dashboard.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while loading admin dashboard.');
    }
  }

  /// List cases via Admin endpoint
  Future<List<CaseListItemModel>> fetchAdminCases({
    int page = 1,
    int pageSize = 20,
    String? status,
    String? riskCategory,
    String? search,
  }) async {
    try {
      final queryParams = <String, String>{
        'page': page.toString(),
        'page_size': pageSize.toString(),
        if (status != null && status.isNotEmpty) 'case_status': status,
        if (riskCategory != null && riskCategory.isNotEmpty) 'risk_category': riskCategory,
        if (search != null && search.isNotEmpty) 'search': search,
      };

      final uri = Uri.parse(ApiConfig.adminCasesUrl).replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: _headers).timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final items = data['items'] as List<dynamic>? ?? [];
        return items.map((e) => CaseListItemModel.fromJson(e as Map<String, dynamic>)).toList();
      } else if (response.statusCode == 401) {
        logout();
        throw const ResponderApiException('Session expired. Please log in again.', statusCode: 401);
      } else if (response.statusCode == 403) {
        throw const ResponderApiException('Access denied. Admin access required.', statusCode: 403);
      } else {
        throw ServerErrorException(statusCode: response.statusCode, userMessage: 'Failed to retrieve cases (${response.statusCode}).');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while retrieving admin cases.');
    }
  }

  /// Fetch full case details via Admin endpoint
  Future<CaseDetailModel> fetchAdminCaseDetail(String caseId) async {
    try {
      final uri = Uri.parse(ApiConfig.adminCaseDetailUrl(caseId));
      final response = await http.get(uri, headers: _headers).timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return CaseDetailModel.fromJson(data);
      } else if (response.statusCode == 401) {
        logout();
        throw const ResponderApiException('Session expired. Please log in again.', statusCode: 401);
      } else if (response.statusCode == 403) {
        throw const ResponderApiException('Access denied. Administrator privileges required.', statusCode: 403);
      } else {
        throw ServerErrorException(statusCode: response.statusCode, userMessage: 'Failed to retrieve case details.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while retrieving case details.');
    }
  }

  /// Update case status via Admin endpoint
  Future<void> adminUpdateCaseStatus(String caseId, String newStatus) async {
    try {
      final uri = Uri.parse(ApiConfig.adminCaseStatusUrl(caseId));
      final response = await http
          .post(
            uri,
            headers: _headers,
            body: jsonEncode({'status': newStatus}),
          )
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body);
        throw ResponderApiException(err['error']?['message']?.toString() ?? 'Failed to update case status.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while updating case status.');
    }
  }

  /// Human decision on AI recommendation via Admin endpoint
  Future<void> adminReviewRecommendation(
    String recId,
    String decision, {
    String? modifiedAction,
    String? modifiedPriority,
    String? note,
  }) async {
    try {
      final uri = Uri.parse(ApiConfig.adminReviewRecommendationUrl(recId));
      final response = await http
          .post(
            uri,
            headers: _headers,
            body: jsonEncode({
              'decision': decision,
              if (modifiedAction != null && modifiedAction.isNotEmpty) 'modified_action': modifiedAction,
              if (modifiedPriority != null && modifiedPriority.isNotEmpty) 'modified_priority': modifiedPriority,
              if (note != null && note.isNotEmpty) 'responder_note': note,
            }),
          )
          .timeout(ApiConfig.timeoutDuration);

      if (response.statusCode != 200) {
        final err = jsonDecode(response.body);
        throw ResponderApiException(err['error']?['message']?.toString() ?? 'Failed to record decision.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while recording recommendation decision.');
    }
  }

  /// Retrieve full audit log via Admin endpoint
  Future<List<AdminAuditItemModel>> fetchAdminAudit({
    int page = 1,
    int pageSize = 50,
    String? caseId,
    String? eventType,
  }) async {
    try {
      final queryParams = <String, String>{
        'page': page.toString(),
        'page_size': pageSize.toString(),
        if (caseId != null && caseId.isNotEmpty) 'case_id': caseId,
        if (eventType != null && eventType.isNotEmpty) 'event_type': eventType,
      };

      final uri = Uri.parse(ApiConfig.adminAuditUrl).replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: _headers).timeout(ApiConfig.timeoutDuration);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as List<dynamic>;
        return data.map((e) => AdminAuditItemModel.fromJson(e as Map<String, dynamic>)).toList();
      } else if (response.statusCode == 401) {
        logout();
        throw const ResponderApiException('Session expired. Please log in again.', statusCode: 401);
      } else if (response.statusCode == 403) {
        throw const ResponderApiException('Access denied. Administrator privileges required.', statusCode: 403);
      } else {
        throw ServerErrorException(statusCode: response.statusCode, userMessage: 'Failed to retrieve audit log.');
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw const NetworkConnectionException(userMessage: 'Network error while retrieving audit log.');
    }
  }

}
