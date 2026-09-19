import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../shared/models/chat_message.dart';
import '../../shared/models/intake_draft.dart';
import '../constants/app_strings.dart';
import '../network/api_config.dart';
import '../network/api_exceptions.dart';
import '../../features/victim/data/models/api_models.dart';
import '../../features/victim/data/services/victim_api_service.dart';

/// Central state management service providing dynamic, non-hardcoded data
/// across the victim intake journey, synchronized with FastAPI backend.
class AppStateService extends ChangeNotifier {
  static final AppStateService instance = AppStateService._internal();
  AppStateService._internal() {
    _loadPersistedLanguage();
  }

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
      await ApiConfig.discoverBaseUrl();
      final session = await _apiService.createSession(language: currentLanguageCode);
      _sessionId = session.sessionId;
      debugPrint('[AppStateService] Connected to backend session: $_sessionId at ${ApiConfig.baseUrl}');
      notifyListeners();
    } catch (e) {
      debugPrint('[AppStateService] Backend session init error ($e)');
      // Graceful local fallback for offline development
      _sessionId ??= 'local-${DateTime.now().millisecondsSinceEpoch}';
    }
  }

  /// Starts a fresh chat session by clearing in-memory messages and resetting the session ID.
  /// On next message send, a new backend session will be created.
  /// (Active chat history auto-restoration is disabled per privacy & UX requirements).
  void startFreshChatSession() {
    _sessionId = null;
    _messages.clear();
    _lastFailedMessage = null;
    _lastFailedInputSource = null;
    debugPrint('[AppStateService] Fresh chat session initialized — active chat empty, ready for new conversation.');
    notifyListeners();
  }

  // --- Language State ---
  String _selectedLanguage = 'English';
  String get selectedLanguage => _selectedLanguage;

  Future<void> _loadPersistedLanguage() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString('nhaa_selected_language');
      if (saved != null && saved.isNotEmpty) {
        _selectedLanguage = saved;
        AppStrings.setLocale(currentLanguageCode);
        notifyListeners();
      }
    } catch (_) {}
  }

  Future<void> _persistLanguage(String lang) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('nhaa_selected_language', lang);
    } catch (_) {}
  }

  void setLanguage(String lang) {
    if (_selectedLanguage != lang) {
      _selectedLanguage = lang;
      AppStrings.setLocale(currentLanguageCode);
      _persistLanguage(lang);
      // Refresh session language with backend
      _sessionId = null;
      initBackendSession();
      notifyListeners();
    }
  }

  void setLanguageDirectly(String lang) {
    if (_selectedLanguage != lang) {
      _selectedLanguage = lang;
      AppStrings.setLocale(currentLanguageCode);
      _persistLanguage(lang);
      notifyListeners();
    }
  }

  // --- Chat State (Clean Initial State, No Mock AI Messages) ---
  final List<ChatMessage> _messages = [];

  List<ChatMessage> get messages => List.unmodifiable(_messages);

  // --- AI Generating & Typing State ---
  bool _isAiGenerating = false;
  bool get isAiGenerating => _isAiGenerating;

  String? _lastFailedMessage;
  String? get lastFailedMessage => _lastFailedMessage;
  String? _lastFailedInputSource;

  Future<void> retryLastMessage() async {
    if (_lastFailedMessage != null) {
      final msg = _lastFailedMessage!;
      final src = _lastFailedInputSource ?? 'text';
      _lastFailedMessage = null;
      _lastFailedInputSource = null;
      await _sendUserMessageInternal(msg, inputSource: src, isRetry: true);
    }
  }

  Future<void> sendUserMessage(String text, {String inputSource = 'text'}) async {
    await _sendUserMessageInternal(text, inputSource: inputSource, isRetry: false);
  }

  Future<void> _sendUserMessageInternal(
    String text, {
    String inputSource = 'text',
    bool isRetry = false,
  }) async {
    if (text.trim().isEmpty) return;

    final trimmed = text.trim();
    final nowIso = DateTime.now().toUtc().toIso8601String();
    if (!isRetry) {
      _messages.add(
        ChatMessage(
          id: 'user-${DateTime.now().millisecondsSinceEpoch}',
          text: trimmed,
          isAssistant: false,
          timestamp: nowIso,
          inputSource: inputSource,
        ),
      );
    }

    _isAiGenerating = true;
    _lastFailedMessage = null;
    _lastFailedInputSource = null;
    notifyListeners();

    try {
      // Ensure active backend session
      if (_sessionId == null || _sessionId!.startsWith('local-')) {
        try {
          await ApiConfig.discoverBaseUrl();
          final session = await _apiService.createSession(language: currentLanguageCode);
          _sessionId = session.sessionId;
          debugPrint('[AppStateService] Connected to backend session: $_sessionId at ${ApiConfig.baseUrl}');
        } catch (e) {
          debugPrint('[AppStateService] Backend session init error ($e)');
        }
      }

      if (_sessionId != null && !_sessionId!.startsWith('local-')) {
        try {
          debugPrint('[CHAT] Session ID: ${_sessionId!.substring(0, 8)}...');
          debugPrint('[CHAT] API URL: ${ApiConfig.sessionMessagesUrl(_sessionId!)}');
          debugPrint('[CHAT] Sending — AI processing started');
          final response = await _apiService.sendMessage(
            sessionId: _sessionId!,
            message: trimmed,
            language: currentLanguageCode,
            inputSource: inputSource.toUpperCase(),
          );

          debugPrint('[CHAT] AI response received — len=${response.response.length}');
          _messages.add(
            ChatMessage(
              id: response.messageId,
              text: response.response,
              isAssistant: true,
              timestamp: response.timestamp ?? DateTime.now().toUtc().toIso8601String(),
            ),
          );
          return;
        } on SessionNotFoundException catch (e) {
          debugPrint('[AppStateService] SessionNotFoundException: $e');
          _sessionId = null;
          _lastFailedMessage = trimmed;
          _lastFailedInputSource = inputSource;
          _messages.add(
            ChatMessage(
              id: 'asst-err-${DateTime.now().millisecondsSinceEpoch}',
              text: "Your session was refreshed. Please tap retry to send your message.",
              isAssistant: true,
              timestamp: DateTime.now().toUtc().toIso8601String(),
            ),
          );
          return;
        } on ApiException catch (e) {
          debugPrint('[AppStateService] ApiException: ${e.userMessage} (${e.technicalDetails})');
          _lastFailedMessage = trimmed;
          _lastFailedInputSource = inputSource;
          _messages.add(
            ChatMessage(
              id: 'asst-err-${DateTime.now().millisecondsSinceEpoch}',
              text: e.userMessage.isNotEmpty ? e.userMessage : "TrueVoice AI is temporarily unavailable. Please try again.",
              isAssistant: true,
              timestamp: DateTime.now().toUtc().toIso8601String(),
            ),
          );
          return;
        } catch (e) {
          debugPrint('[AppStateService] Unhandled network error: $e');
          _lastFailedMessage = trimmed;
          _lastFailedInputSource = inputSource;
          _messages.add(
            ChatMessage(
              id: 'asst-err-${DateTime.now().millisecondsSinceEpoch}',
              text: "TrueVoice AI is temporarily unavailable. Please try again.",
              isAssistant: true,
              timestamp: DateTime.now().toUtc().toIso8601String(),
            ),
          );
          return;
        }
      }

      // No backend connection available - surface explicit unavailable state without fake fallback
      _lastFailedMessage = trimmed;
      _lastFailedInputSource = inputSource;
      _messages.add(
        ChatMessage(
          id: 'asst-err-${DateTime.now().millisecondsSinceEpoch}',
          text: "TrueVoice AI is temporarily unavailable. Please check your connection and tap retry.",
          isAssistant: true,
          timestamp: DateTime.now().toUtc().toIso8601String(),
        ),
      );
    } finally {
      _isAiGenerating = false;
      notifyListeners();
    }
  }

  void clearChat() {
    startFreshChatSession();
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

  void setConsentAgreedDirectly(bool agreed) {
    _consentAgreed = agreed;
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
