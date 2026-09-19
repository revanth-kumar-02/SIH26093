// Typed DTO models matching FastAPI backend schemas for victim interactions.

class BackendSession {
  final String sessionId;
  final String language;
  final String status;
  final String? createdAt;

  const BackendSession({
    required this.sessionId,
    required this.language,
    required this.status,
    this.createdAt,
  });

  factory BackendSession.fromJson(Map<String, dynamic> json) {
    return BackendSession(
      sessionId: json['session_id'] as String? ?? '',
      language: json['language'] as String? ?? 'en',
      status: json['status'] as String? ?? 'active',
      createdAt: json['created_at'] as String?,
    );
  }
}

class BackendChatMessage {
  final String messageId;
  final String response;
  final String status;
  final String? timestamp;

  const BackendChatMessage({
    required this.messageId,
    required this.response,
    required this.status,
    this.timestamp,
  });

  factory BackendChatMessage.fromJson(Map<String, dynamic> json) {
    return BackendChatMessage(
      messageId: json['message_id'] as String? ?? '',
      response: json['response'] as String? ?? '',
      status: json['status'] as String? ?? 'received',
      timestamp: json['timestamp'] as String?,
    );
  }
}

class BackendAssessment {
  final String sessionId;
  final String status;
  final String riskLevel;
  final double? svi;
  final List<String> indicators;

  const BackendAssessment({
    required this.sessionId,
    required this.status,
    required this.riskLevel,
    this.svi,
    required this.indicators,
  });

  factory BackendAssessment.fromJson(Map<String, dynamic> json) {
    final assessmentMap = json['assessment'] as Map<String, dynamic>? ?? {};
    final indicatorsList = (assessmentMap['indicators'] as List<dynamic>?)
            ?.map((e) => e.toString())
            .toList() ??
        [];

    return BackendAssessment(
      sessionId: json['session_id'] as String? ?? '',
      status: json['status'] as String? ?? 'pending_review',
      riskLevel: assessmentMap['risk_level'] as String? ?? 'not_available',
      svi: (assessmentMap['svi'] as num?)?.toDouble(),
      indicators: indicatorsList,
    );
  }
}

class BackendTranscription {
  final String sessionId;
  final String text;
  final String transcript;
  final String? language;
  final String? decoder;
  final String status;
  final String? timestamp;
  final SpeechEmotionResult? speechEmotion;

  const BackendTranscription({
    required this.sessionId,
    required this.text,
    required this.transcript,
    this.language,
    this.decoder,
    required this.status,
    this.timestamp,
    this.speechEmotion,
  });

  factory BackendTranscription.fromJson(Map<String, dynamic> json) {
    final rawText = (json['transcript'] ?? json['text']) as String? ?? '';
    final emotionJson = json['speech_emotion'] as Map<String, dynamic>?;
    return BackendTranscription(
      sessionId: json['session_id'] as String? ?? '',
      text: rawText,
      transcript: rawText,
      language: json['language'] as String?,
      decoder: json['decoder'] as String? ?? 'ctc',
      status: json['status'] as String? ?? 'completed',
      timestamp: json['timestamp'] as String?,
      speechEmotion: emotionJson != null ? SpeechEmotionResult.fromJson(emotionJson) : null,
    );
  }
}

class SpeechEmotionResult {
  final String emotion;
  final Map<String, double> probabilities;
  final String? modelVersion;
  final double? durationMs;
  final String? device;

  const SpeechEmotionResult({
    required this.emotion,
    required this.probabilities,
    this.modelVersion,
    this.durationMs,
    this.device,
  });

  factory SpeechEmotionResult.fromJson(Map<String, dynamic> json) {
    final rawProbs = json['probabilities'] as Map<String, dynamic>? ?? {};
    final Map<String, double> probs = {};
    rawProbs.forEach((key, val) {
      if (val is num) {
        probs[key] = val.toDouble();
      }
    });

    return SpeechEmotionResult(
      emotion: json['emotion'] as String? ?? 'calm',
      probabilities: probs,
      modelVersion: json['model_version'] as String?,
      durationMs: (json['duration_ms'] as num?)?.toDouble(),
      device: json['device'] as String?,
    );
  }
}

class EmotionScore {
  final String label;
  final double score;

  const EmotionScore({
    required this.label,
    required this.score,
  });

  factory EmotionScore.fromJson(Map<String, dynamic> json) {
    return EmotionScore(
      label: json['label'] as String? ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class TextEmotionResult {
  final List<EmotionScore> emotions;
  final String? topEmotion;
  final String? modelVersion;
  final double? durationMs;
  final String? device;

  const TextEmotionResult({
    required this.emotions,
    this.topEmotion,
    this.modelVersion,
    this.durationMs,
    this.device,
  });

  factory TextEmotionResult.fromJson(Map<String, dynamic> json) {
    final rawEmotions = json['emotions'] as List<dynamic>? ?? [];
    final list = rawEmotions
        .map((e) => EmotionScore.fromJson(e as Map<String, dynamic>))
        .toList();

    return TextEmotionResult(
      emotions: list,
      topEmotion: json['top_emotion'] as String?,
      modelVersion: json['model_version'] as String?,
      durationMs: (json['duration_ms'] as num?)?.toDouble(),
      device: json['device'] as String?,
    );
  }
}

class BackendPersistedMessage {
  final String messageId;
  final String senderType;
  final String content;
  final String inputSource;
  final String timestamp;
  final String? language;

  const BackendPersistedMessage({
    required this.messageId,
    required this.senderType,
    required this.content,
    required this.inputSource,
    required this.timestamp,
    this.language,
  });

  factory BackendPersistedMessage.fromJson(Map<String, dynamic> json) {
    return BackendPersistedMessage(
      messageId: json['message_id'] as String? ?? '',
      senderType: json['sender_type'] as String? ?? 'user',
      content: json['content'] as String? ?? '',
      inputSource: json['input_source'] as String? ?? 'text',
      timestamp: json['timestamp'] as String? ?? '',
      language: json['language'] as String?,
    );
  }
}

class VerifiedEmergencyResourceModel {
  final String title;
  final String number;
  final String description;

  const VerifiedEmergencyResourceModel({
    required this.title,
    required this.number,
    required this.description,
  });

  factory VerifiedEmergencyResourceModel.fromJson(Map<String, dynamic> json) {
    return VerifiedEmergencyResourceModel(
      title: json['title'] as String? ?? 'National Emergency',
      number: json['number'] as String? ?? '112',
      description: json['description'] as String? ?? '',
    );
  }
}

class SupportRecommendationModel {
  final String recommendationId;
  final String category;
  final String priority;
  final String reason;
  final List<String> supportingIndicators;
  final String responderAction;
  final bool requiresHumanReview;

  const SupportRecommendationModel({
    required this.recommendationId,
    required this.category,
    required this.priority,
    required this.reason,
    required this.supportingIndicators,
    required this.responderAction,
    required this.requiresHumanReview,
  });

  factory SupportRecommendationModel.fromJson(Map<String, dynamic> json) {
    final rawIndicators = json['supporting_indicators'] as List<dynamic>? ?? [];
    return SupportRecommendationModel(
      recommendationId: json['recommendation_id'] as String? ?? '',
      category: json['category'] as String? ?? '',
      priority: json['priority'] as String? ?? 'routine',
      reason: json['reason'] as String? ?? '',
      supportingIndicators: rawIndicators.map((e) => e.toString()).toList(),
      responderAction: json['responder_action'] as String? ?? '',
      requiresHumanReview: json['requires_human_review'] as bool? ?? true,
    );
  }

  String get displayTitle {
    switch (category) {
      case 'COUNSELLING_SUPPORT':
        return 'Counselling Support';
      case 'SAFETY_ASSISTANCE':
        return 'Safety Planning & Assistance';
      case 'LEGAL_AID':
        return 'Confidential Legal Guidance';
      case 'SOCIAL_SUPPORT':
        return 'Social & Shelter Support';
      case 'MEDICAL_ASSISTANCE':
        return 'Medical Attention Referral';
      case 'EMERGENCY_SUPPORT':
        return 'Immediate Emergency Protection';
      case 'POLICE_ASSISTANCE':
        return 'Special Police Liaison Review';
      default:
        return category.replaceAll('_', ' ');
    }
  }
}

class PersonalizedSupportPlanModel {
  final String sessionId;
  final String whatWeHeard;
  final String howYouAreDoing;
  final List<String> primaryConcerns;
  final List<String> emotionalIndicators;
  final bool immediateSafetyNeeded;
  final String? immediateSafetyMessage;
  final VerifiedEmergencyResourceModel? verifiedEmergencyResource;
  final List<SupportRecommendationModel> recommendations;
  final bool hasHumanAssignment;
  final String humanReviewStatus;
  final String humanReviewMessage;
  final List<Map<String, String>> userChoices;
  final List<String> uncertainties;
  final String createdAt;

  const PersonalizedSupportPlanModel({
    required this.sessionId,
    required this.whatWeHeard,
    required this.howYouAreDoing,
    required this.primaryConcerns,
    required this.emotionalIndicators,
    required this.immediateSafetyNeeded,
    this.immediateSafetyMessage,
    this.verifiedEmergencyResource,
    required this.recommendations,
    required this.hasHumanAssignment,
    required this.humanReviewStatus,
    required this.humanReviewMessage,
    required this.userChoices,
    required this.uncertainties,
    required this.createdAt,
  });

  factory PersonalizedSupportPlanModel.fromJson(Map<String, dynamic> json) {
    final rawRecs = json['recommendations'] as List<dynamic>? ?? [];
    final recs = rawRecs
        .map((r) => SupportRecommendationModel.fromJson(r as Map<String, dynamic>))
        .toList();

    final emJson = json['verified_emergency_resource'] as Map<String, dynamic>?;
    final verifiedEm = emJson != null ? VerifiedEmergencyResourceModel.fromJson(emJson) : null;

    final rawChoices = json['user_choices'] as List<dynamic>? ?? [];
    final choices = rawChoices.map((c) {
      if (c is Map) {
        return c.map((k, v) => MapEntry(k.toString(), v.toString()));
      }
      return <String, String>{};
    }).toList();

    return PersonalizedSupportPlanModel(
      sessionId: json['session_id'] as String? ?? '',
      whatWeHeard: json['what_we_heard'] as String? ?? '',
      howYouAreDoing: json['how_you_are_doing'] as String? ?? '',
      primaryConcerns: (json['primary_concerns'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
      emotionalIndicators: (json['emotional_indicators'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
      immediateSafetyNeeded: json['immediate_safety_needed'] as bool? ?? false,
      immediateSafetyMessage: json['immediate_safety_message'] as String?,
      verifiedEmergencyResource: verifiedEm,
      recommendations: recs,
      hasHumanAssignment: json['has_human_assignment'] as bool? ?? false,
      humanReviewStatus: json['human_review_status'] as String? ?? 'Human review recommended',
      humanReviewMessage: json['human_review_message'] as String? ?? '',
      userChoices: choices,
      uncertainties: (json['uncertainties'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

