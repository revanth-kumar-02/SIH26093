import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_config.dart';
import '../models/api_models.dart';

/// Dedicated service for victim-side interactions with the FastAPI backend.
class VictimApiService {
  final ApiClient _client;

  VictimApiService({ApiClient? client}) : _client = client ?? ApiClient();

  /// Health check validation
  Future<bool> checkHealth() async {
    try {
      final res = await _client.get(ApiConfig.healthUrl);
      return res['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }

  /// Create a new backend session for victim intake
  Future<BackendSession> createSession({String language = 'en'}) async {
    final res = await _client.post(
      ApiConfig.sessionsUrl,
      body: {'language': language},
    );
    return BackendSession.fromJson(res);
  }

  /// Retrieve persisted messages from PostgreSQL backend for session continuity
  Future<List<BackendPersistedMessage>> getPersistedMessages({
    required String sessionId,
  }) async {
    try {
      final res = await _client.get(ApiConfig.sessionMessagesUrl(sessionId));
      final dynamic rawList = res['data'] ?? res['messages'];
      if (rawList is List) {
        return rawList
            .map((m) => BackendPersistedMessage.fromJson(m as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  /// Send message to backend and receive mock AI response
  Future<BackendChatMessage> sendMessage({
    required String sessionId,
    required String message,
  }) async {
    final res = await _client.post(
      ApiConfig.sessionMessagesUrl(sessionId),
      body: {'message': message},
    );
    return BackendChatMessage.fromJson(res);
  }

  /// Request assessment placeholder establishing the Phase 3 contract
  Future<BackendAssessment> requestAssessment({
    required String sessionId,
  }) async {
    final res = await _client.post(
      ApiConfig.sessionAssessmentUrl(sessionId),
    );
    return BackendAssessment.fromJson(res);
  }

  /// Upload recorded audio bytes for ASR transcription
  Future<BackendTranscription> transcribeAudio({
    required String sessionId,
    required List<int> audioBytes,
    required String filename,
    String? language,
    String? decoder,
  }) async {
    final fields = <String, String>{};
    if (language != null && language.isNotEmpty) {
      fields['language'] = language;
    }
    if (decoder != null && decoder.isNotEmpty) {
      fields['decoder'] = decoder;
    }

    final res = await _client.postMultipart(
      ApiConfig.sessionTranscribeUrl(sessionId),
      fileBytes: audioBytes,
      filename: filename,
      fieldName: 'audio',
      fields: fields,
    );

    return BackendTranscription.fromJson(res);
  }

  /// Analyze text emotion across GoEmotions taxonomy
  Future<TextEmotionResult> analyzeText({
    required String sessionId,
    required String text,
  }) async {
    final res = await _client.post(
      ApiConfig.sessionAnalyzeTextUrl(sessionId),
      body: {'text': text},
    );
    return TextEmotionResult.fromJson(res);
  }

  /// Analyze speech emotion across 7 Wav2Vec2 classes
  Future<SpeechEmotionResult> analyzeAudio({
    required String sessionId,
    required List<int> audioBytes,
    required String filename,
  }) async {
    final res = await _client.postMultipart(
      ApiConfig.sessionAnalyzeAudioUrl(sessionId),
      fileBytes: audioBytes,
      filename: filename,
      fieldName: 'audio',
    );
    return SpeechEmotionResult.fromJson(res);
  }
}
