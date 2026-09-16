class ResponderAuthSession {
  final String accessToken;
  final String refreshToken;
  final String role;
  final String displayName;
  final String responderId;

  const ResponderAuthSession({
    required this.accessToken,
    required this.refreshToken,
    required this.role,
    required this.displayName,
    required this.responderId,
  });

  factory ResponderAuthSession.fromJson(Map<String, dynamic> json) {
    return ResponderAuthSession(
      accessToken: json['access_token'] as String? ?? '',
      refreshToken: json['refresh_token'] as String? ?? '',
      role: json['role'] as String? ?? 'PEOPLE',
      displayName: json['display_name'] as String? ?? 'Responder',
      responderId: json['responder_id'] as String? ?? '',
    );
  }
}

class CaseListItemModel {
  final String id;
  final String externalCaseReference;
  final String status;
  final String language;
  final String consentStatus;
  final String? assignedResponderId;
  final String? assignedResponderName;
  final DateTime createdAt;
  final DateTime updatedAt;
  final double? latestSviScore;
  final String? latestRiskCategory;
  final bool immediateSafetyAttention;
  final bool urgentHumanReview;

  const CaseListItemModel({
    required this.id,
    required this.externalCaseReference,
    required this.status,
    required this.language,
    required this.consentStatus,
    this.assignedResponderId,
    this.assignedResponderName,
    required this.createdAt,
    required this.updatedAt,
    this.latestSviScore,
    this.latestRiskCategory,
    this.immediateSafetyAttention = false,
    this.urgentHumanReview = false,
  });

  factory CaseListItemModel.fromJson(Map<String, dynamic> json) {
    return CaseListItemModel(
      id: json['id'] as String? ?? '',
      externalCaseReference: json['external_case_reference'] as String? ?? '',
      status: json['status'] as String? ?? 'NEW',
      language: json['language'] as String? ?? 'en',
      consentStatus: json['consent_status'] as String? ?? '',
      assignedResponderId: json['assigned_responder_id'] as String?,
      assignedResponderName: json['assigned_responder_name'] as String?,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
      updatedAt: DateTime.tryParse(json['updated_at'] as String? ?? '') ?? DateTime.now(),
      latestSviScore: (json['latest_svi_score'] as num?)?.toDouble(),
      latestRiskCategory: json['latest_risk_category'] as String?,
      immediateSafetyAttention: json['immediate_safety_attention'] as bool? ?? false,
      urgentHumanReview: json['urgent_human_review'] as bool? ?? false,
    );
  }
}

class RecommendationItemModel {
  final String id;
  final String category;
  final String priority;
  final String reason;
  final List<String> supportingIndicators;
  final List<String> evidenceSources;
  final String responderAction;
  final bool requiresHumanReview;
  final String status;
  final String? responderDecision;
  final String? responderNote;
  final DateTime createdAt;
  final DateTime? reviewedAt;
  final String? reviewedBy;

  const RecommendationItemModel({
    required this.id,
    required this.category,
    required this.priority,
    required this.reason,
    required this.supportingIndicators,
    required this.evidenceSources,
    required this.responderAction,
    required this.requiresHumanReview,
    required this.status,
    this.responderDecision,
    this.responderNote,
    required this.createdAt,
    this.reviewedAt,
    this.reviewedBy,
  });

  factory RecommendationItemModel.fromJson(Map<String, dynamic> json) {
    return RecommendationItemModel(
      id: json['id'] as String? ?? '',
      category: json['category'] as String? ?? 'SUPPORT',
      priority: json['priority'] as String? ?? 'STANDARD',
      reason: json['reason'] as String? ?? '',
      supportingIndicators: (json['supporting_indicators'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      evidenceSources: (json['evidence_sources'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      responderAction: json['responder_action'] as String? ?? '',
      requiresHumanReview: json['requires_human_review'] as bool? ?? true,
      status: json['status'] as String? ?? 'PENDING',
      responderDecision: json['responder_decision'] as String?,
      responderNote: json['responder_note'] as String?,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
      reviewedAt: json['reviewed_at'] != null ? DateTime.tryParse(json['reviewed_at'] as String) : null,
      reviewedBy: json['reviewed_by'] as String?,
    );
  }
}

class AuditEventModel {
  final String id;
  final String eventType;
  final String actorId;
  final String actorType;
  final String entityType;
  final String? entityId;
  final Map<String, dynamic> metadata;
  final DateTime createdAt;

  const AuditEventModel({
    required this.id,
    required this.eventType,
    required this.actorId,
    required this.actorType,
    required this.entityType,
    this.entityId,
    required this.metadata,
    required this.createdAt,
  });

  factory AuditEventModel.fromJson(Map<String, dynamic> json) {
    return AuditEventModel(
      id: json['id'] as String? ?? '',
      eventType: json['event_type'] as String? ?? '',
      actorId: json['actor_id'] as String? ?? '',
      actorType: json['actor_type'] as String? ?? '',
      entityType: json['entity_type'] as String? ?? '',
      entityId: json['entity_id'] as String?,
      metadata: json['event_metadata'] as Map<String, dynamic>? ?? {},
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
    );
  }
}

class CaseDetailModel {
  final String id;
  final String externalCaseReference;
  final String status;
  final String language;
  final String consentStatus;
  final String? assignedResponderName;
  final DateTime createdAt;
  final DateTime updatedAt;
  final bool immediateSafetyAttention;
  final bool urgentHumanReview;
  final double? sviScore;
  final String? riskCategory;
  final Map<String, dynamic> factorContributions;
  final List<String> keyDrivers;
  final List<String> uncertainties;
  final String? aiSummary;
  final List<dynamic> aiIndicators;
  final List<Map<String, dynamic>> messages;
  final List<RecommendationItemModel> recommendations;
  final List<AuditEventModel> auditHistory;

  const CaseDetailModel({
    required this.id,
    required this.externalCaseReference,
    required this.status,
    required this.language,
    required this.consentStatus,
    this.assignedResponderName,
    required this.createdAt,
    required this.updatedAt,
    this.immediateSafetyAttention = false,
    this.urgentHumanReview = false,
    this.sviScore,
    this.riskCategory,
    this.factorContributions = const {},
    this.keyDrivers = const [],
    this.uncertainties = const [],
    this.aiSummary,
    this.aiIndicators = const [],
    this.messages = const [],
    this.recommendations = const [],
    this.auditHistory = const [],
  });

  factory CaseDetailModel.fromJson(Map<String, dynamic> json) {
    final safetyFlags = json['safety_flags'] as Map<String, dynamic>? ?? {};
    final svi = json['svi_result'] as Map<String, dynamic>?;
    final assessment = json['ai_assessment'] as Map<String, dynamic>?;
    final conv = json['conversation_summary'] as Map<String, dynamic>?;
    final responderInfo = json['assigned_responder'] as Map<String, dynamic>?;

    return CaseDetailModel(
      id: json['id'] as String? ?? '',
      externalCaseReference: json['external_case_reference'] as String? ?? '',
      status: json['status'] as String? ?? 'NEW',
      language: json['language'] as String? ?? 'en',
      consentStatus: json['consent_status'] as String? ?? '',
      assignedResponderName: responderInfo?['display_name'] as String?,
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
      updatedAt: DateTime.tryParse(json['updated_at'] as String? ?? '') ?? DateTime.now(),
      immediateSafetyAttention: safetyFlags['immediate_safety_attention'] as bool? ?? false,
      urgentHumanReview: safetyFlags['urgent_human_review'] as bool? ?? false,
      sviScore: (svi?['score'] as num?)?.toDouble(),
      riskCategory: svi?['risk_category'] as String?,
      factorContributions: svi?['factor_contributions'] as Map<String, dynamic>? ?? {},
      keyDrivers: (svi?['key_drivers'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      uncertainties: (svi?['uncertainties'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      aiSummary: assessment?['clinical_summary'] as String?,
      aiIndicators: (assessment?['indicators'] as List<dynamic>?) ?? [],
      messages: (conv?['messages'] as List<dynamic>?)?.map((m) => m as Map<String, dynamic>).toList() ?? [],
      recommendations: (json['recommendations'] as List<dynamic>?)
              ?.map((r) => RecommendationItemModel.fromJson(r as Map<String, dynamic>))
              .toList() ??
          [],
      auditHistory: (json['audit_history'] as List<dynamic>?)
              ?.map((a) => AuditEventModel.fromJson(a as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}


class DashboardAnalyticsModel {
  final int activeCases;
  final int urgentReview;
  final int highRisk;
  final int pendingReviews;
  final Map<String, int> riskDistribution;
  final List<CaseListItemModel> requiresAttentionCases;
  final List<CaseListItemModel> recentCases;

  const DashboardAnalyticsModel({
    required this.activeCases,
    required this.urgentReview,
    required this.highRisk,
    required this.pendingReviews,
    required this.riskDistribution,
    required this.requiresAttentionCases,
    required this.recentCases,
  });

  factory DashboardAnalyticsModel.fromJson(Map<String, dynamic> json) {
    final distMap = json['risk_distribution'] as Map<String, dynamic>? ?? {};
    final parsedDist = distMap.map((k, v) => MapEntry(k, (v as num).toInt()));

    final attentionList = (json['requires_attention_cases'] as List<dynamic>?)
            ?.map((e) => CaseListItemModel.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];

    final recentList = (json['recent_cases'] as List<dynamic>?)
            ?.map((e) => CaseListItemModel.fromJson(e as Map<String, dynamic>))
            .toList() ??
        [];

    return DashboardAnalyticsModel(
      activeCases: (json['active_cases'] as num?)?.toInt() ?? 0,
      urgentReview: (json['urgent_review'] as num?)?.toInt() ?? 0,
      highRisk: (json['high_risk'] as num?)?.toInt() ?? 0,
      pendingReviews: (json['pending_reviews'] as num?)?.toInt() ?? 0,
      riskDistribution: parsedDist,
      requiresAttentionCases: attentionList,
      recentCases: recentList,
    );
  }
}

class AdminAuditItemModel {
  final String id;
  final DateTime timestamp;
  final String actor;
  final String actorId;
  final String actorType;
  final String event;
  final String entity;
  final String? entityId;
  final String? caseReference;
  final String? caseId;
  final Map<String, dynamic> details;

  const AdminAuditItemModel({
    required this.id,
    required this.timestamp,
    required this.actor,
    required this.actorId,
    required this.actorType,
    required this.event,
    required this.entity,
    this.entityId,
    this.caseReference,
    this.caseId,
    required this.details,
  });

  factory AdminAuditItemModel.fromJson(Map<String, dynamic> json) {
    return AdminAuditItemModel(
      id: json['id'] as String? ?? '',
      timestamp: DateTime.tryParse(json['timestamp'] as String? ?? '') ?? DateTime.now(),
      actor: json['actor'] as String? ?? 'ADMIN',
      actorId: json['actor_id'] as String? ?? '',
      actorType: json['actor_type'] as String? ?? 'ADMIN',
      event: json['event'] as String? ?? '',
      entity: json['entity'] as String? ?? '',
      entityId: json['entity_id'] as String?,
      caseReference: json['case_reference'] as String?,
      caseId: json['case_id'] as String?,
      details: json['details'] as Map<String, dynamic>? ?? {},
    );
  }
}
