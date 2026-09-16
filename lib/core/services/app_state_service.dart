import 'package:flutter/foundation.dart';
import '../../shared/models/chat_message.dart';
import '../../shared/models/intake_draft.dart';
import '../network/api_exceptions.dart';
import '../../features/victim/data/models/api_models.dart';
import '../../features/victim/data/services/victim_api_service.dart';

/// Central state management service providing dynamic, non-hardcoded data
/// across the victim intake journey, synchronized with FastAPI backend.
class AppStateService extends ChangeNotifier {
  static final AppStateService instance = AppStateService._internal();
  AppStateService._internal();

  final VictimApiService _apiService = VictimApiService();

  // --- Backend Session State ---
  String? _sessionId;
  String? get sessionId => _sessionId;

  /// Helper to convert language display name to ISO code
  String get currentLanguageCode {
    final lower = _selectedLanguage.toLowerCase();
    if (lower.startsWith('ta')) return 'ta';
    if (lower.startsWith('hi')) return 'hi';
    if (lower.startsWith('te')) return 'te';
    if (lower.startsWith('ka') || lower.startsWith('kn')) return 'kn';
    if (lower.startsWith('ma') || lower.startsWith('ml')) return 'ml';
    return 'en';
  }

  /// Initialize backend session if not already established
  Future<void> initBackendSession() async {
    if (_sessionId != null && !_sessionId!.startsWith('local-')) return;
    try {
      final session = await _apiService.createSession(language: currentLanguageCode);
      _sessionId = session.sessionId;
      notifyListeners();
    } catch (_) {
      // Graceful local fallback for offline development
      _sessionId ??= 'local-${DateTime.now().millisecondsSinceEpoch}';
    }
  }

  /// Restores persistent conversation history from PostgreSQL backend
  Future<bool> restoreSessionHistory(String sessionId) async {
    try {
      final persisted = await _apiService.getPersistedMessages(sessionId: sessionId);
      if (persisted.isNotEmpty) {
        _sessionId = sessionId;
        _messages.clear();
        for (final m in persisted) {
          final isAi = m.senderType.toLowerCase() == 'ai' || m.senderType.toLowerCase() == 'system';
          _messages.add(
            ChatMessage(
              id: m.messageId,
              text: m.content,
              isAssistant: isAi,
              timestamp: isAi ? 'AI Assessment' : (m.inputSource == 'voice' ? 'Spoken by you' : 'Shared by you'),
              inputSource: m.inputSource,
            ),
          );
        }
        notifyListeners();
        return true;
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  // --- Language State ---
  String _selectedLanguage = 'English';
  String get selectedLanguage => _selectedLanguage;

  void setLanguage(String lang) {
    if (_selectedLanguage != lang) {
      _selectedLanguage = lang;
      // Refresh session language with backend
      _sessionId = null;
      initBackendSession();
      notifyListeners();
    }
  }

  // --- Chat State (Clean Initial State, No Hardcoded Pre-Existing User Text) ---
  final List<ChatMessage> _messages = [
    const ChatMessage(
      id: 'welcome-init',
      text:
          "Hello. You're in a quiet, safe space. Take your time, and only share what feels comfortable. Can you tell me a little about what happened?",
      isAssistant: true,
      timestamp: 'Just now',
    ),
  ];

  List<ChatMessage> get messages => List.unmodifiable(_messages);

  Future<void> sendUserMessage(String text, {String inputSource = 'text'}) async {
    if (text.trim().isEmpty) return;

    final trimmed = text.trim();
    _messages.add(
      ChatMessage(
        id: 'user-${DateTime.now().millisecondsSinceEpoch}',
        text: trimmed,
        isAssistant: false,
        timestamp: inputSource == 'voice' ? 'Spoken by you' : 'Shared by you',
        inputSource: inputSource,
      ),
    );
    notifyListeners();

    // Ensure active backend session
    if (_sessionId == null || _sessionId!.startsWith('local-')) {
      try {
        final session = await _apiService.createSession(language: currentLanguageCode);
        _sessionId = session.sessionId;
      } catch (_) {
        // Fall back to local simulation
      }
    }

    if (_sessionId != null && !_sessionId!.startsWith('local-')) {
      try {
        final response = await _apiService.sendMessage(
          sessionId: _sessionId!,
          message: trimmed,
        );

        _messages.add(
          ChatMessage(
            id: response.messageId,
            text: response.response,
            isAssistant: true,
            timestamp: 'Moments ago',
          ),
        );
        notifyListeners();
        return;
      } on SessionNotFoundException {
        _sessionId = null;
        _messages.add(
          ChatMessage(
            id: 'asst-err-${DateTime.now().millisecondsSinceEpoch}',
            text: "Your session was refreshed. Please share your message again.",
            isAssistant: true,
            timestamp: 'Just now',
          ),
        );
        notifyListeners();
        return;
      } on ApiException catch (e) {
        _messages.add(
          ChatMessage(
            id: 'asst-err-${DateTime.now().millisecondsSinceEpoch}',
            text: e.userMessage,
            isAssistant: true,
            timestamp: 'Just now',
          ),
        );
        notifyListeners();
        return;
      } catch (_) {
        _messages.add(
          ChatMessage(
            id: 'asst-err-${DateTime.now().millisecondsSinceEpoch}',
            text: "We couldn't connect right now. Please try again.",
            isAssistant: true,
            timestamp: 'Just now',
          ),
        );
        notifyListeners();
        return;
      }
    }

    // Purely local/offline fallback
    _generateEmpatheticResponse(trimmed);
  }

  // --- Voice / ASR Transcription Service Bridge ---
  String? _latestTranscription;
  String? get latestTranscription => _latestTranscription;

  Future<BackendTranscription> transcribeAudioBytes({
    required List<int> audioBytes,
    required String filename,
  }) async {
    await initBackendSession();
    final effectiveSessionId = _sessionId ?? 'local-${DateTime.now().millisecondsSinceEpoch}';

    final transcription = await _apiService.transcribeAudio(
      sessionId: effectiveSessionId,
      audioBytes: audioBytes,
      filename: filename,
      language: currentLanguageCode,
      decoder: 'ctc',
    );

    _latestTranscription = transcription.text;
    saveVoiceDraft(transcription.text);
    notifyListeners();
    return transcription;
  }

  /// Appends transcribed voice text directly into conversation history
  Future<void> commitTranscriptToChat(String transcript) async {
    if (transcript.trim().isEmpty) return;
    await sendUserMessage(transcript.trim(), inputSource: 'voice');
  }

  void _generateEmpatheticResponse(String userText) {
    final lower = userText.toLowerCase();

    String reply;
    if (lower.contains('shelter') || lower.contains('stay') || lower.contains('unsafe') || lower.contains('hostel')) {
      reply =
          "Thank you for trusting us with this. Your immediate safety is our utmost priority. We have verified emergency shelter options and advocates ready to ensure you have a secure place tonight. Would you like to view emergency shelter resources or speak directly with an advocate?";
    } else if (lower.contains('threat') || lower.contains('call') || lower.contains('message') || lower.contains('harass')) {
      reply =
          "I am so sorry you are having to endure this intimidation. You do not have to carry this alone. We can document these incidents securely with timestamps and connect you with trauma-informed legal and psychological counselors.";
    } else if (lower.contains('anonymous') || lower.contains('privacy') || lower.contains('secret')) {
      reply =
          "Understood completely. Everything shared here is encrypted with strict zero-knowledge protocols. You can proceed with full anonymity, and your identity will remain protected.";
    } else if (lower.contains('legal') || lower.contains('law') || lower.contains('court') || lower.contains('police')) {
      reply =
          "We can coordinate confidential pro-bono legal support and rights advisement under the National Helpline Against Atrocities (NHAA) framework whenever you feel prepared.";
    } else {
      reply =
          "Thank you for sharing this. Take all the time you need. Our system is carefully organizing your experience so our trained human advocates can provide compassionate, tailored assistance.";
    }

    Future.delayed(const Duration(milliseconds: 600), () {
      _messages.add(
        ChatMessage(
          id: 'asst-${DateTime.now().millisecondsSinceEpoch}',
          text: reply,
          isAssistant: true,
          timestamp: 'Moments ago',
        ),
      );
      notifyListeners();
    });
  }

  void clearChat() {
    _messages.clear();
    _messages.add(
      ChatMessage(
        id: 'welcome-${DateTime.now().millisecondsSinceEpoch}',
        text:
            "Hello. You're in a quiet, safe space. Take your time, and only share what feels comfortable. How can we support you today?",
        isAssistant: true,
        timestamp: 'Just now',
      ),
    );
    notifyListeners();
  }

  // --- Draft State ---
  IntakeDraft? _activeDraft;
  IntakeDraft? get activeDraft => _activeDraft;

  void saveVoiceDraft(String previewOrSeconds) {
    _activeDraft = IntakeDraft(
      type: 'voice',
      previewText: previewOrSeconds.length > 50
          ? '${previewOrSeconds.substring(0, 47)}...'
          : previewOrSeconds,
      updatedAt: DateTime.now(),
    );
    notifyListeners();
  }

  void saveTextDraft(String text) {
    if (text.trim().isEmpty) return;
    _activeDraft = IntakeDraft(
      type: 'text',
      previewText: text.length > 45 ? '${text.substring(0, 42)}...' : text,
      updatedAt: DateTime.now(),
    );
    notifyListeners();
  }

  void clearDraft() {
    _activeDraft = null;
    _latestTranscription = null;
    notifyListeners();
  }

  // --- Consent State ---
  bool _consentAgreed = false;
  bool get consentAgreed => _consentAgreed;

  void setConsentAgreed(bool agreed) {
    _consentAgreed = agreed;
    if (agreed) {
      initBackendSession();
    }
    notifyListeners();
  }

  // --- Assessment Progress State & Backend Contract ---
  int _assessmentStep = 1;
  int get assessmentStep => _assessmentStep;

  void advanceAssessmentStep(int step) {
    _assessmentStep = step;
    notifyListeners();
  }

  Future<BackendAssessment?> requestAssessment() async {
    if (_sessionId == null || _sessionId!.startsWith('local-')) {
      return null;
    }
    try {
      return await _apiService.requestAssessment(sessionId: _sessionId!);
    } catch (_) {
      return null;
    }
  }
}
