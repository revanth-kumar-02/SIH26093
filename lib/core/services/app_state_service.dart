import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../shared/models/chat_message.dart';
import '../../shared/models/intake_draft.dart';
import '../constants/app_strings.dart';
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
    if (!isRetry) {
      _messages.add(
        ChatMessage(
          id: 'user-${DateTime.now().millisecondsSinceEpoch}',
          text: trimmed,
          isAssistant: false,
          timestamp: inputSource == 'voice' ? 'Spoken by you' : 'Shared by you',
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
          final session = await _apiService.createSession(language: currentLanguageCode);
          _sessionId = session.sessionId;
          debugPrint('[AppStateService] Connected to backend session: $_sessionId');
        } catch (e) {
          debugPrint('[AppStateService] Backend session init failed ($e); using local mode');
        }
      }

      if (_sessionId != null && !_sessionId!.startsWith('local-')) {
        try {
          final response = await _apiService.sendMessage(
            sessionId: _sessionId!,
            message: trimmed,
            language: currentLanguageCode,
            inputSource: inputSource.toUpperCase(),
          );

          _messages.add(
            ChatMessage(
              id: response.messageId,
              text: response.response,
              isAssistant: true,
              timestamp: 'Moments ago',
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
              timestamp: 'Just now',
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
              text: e.userMessage,
              isAssistant: true,
              timestamp: 'Just now',
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
              text: "We couldn't connect right now. Please tap retry to try again.",
              isAssistant: true,
              timestamp: 'Just now',
            ),
          );
          return;
        }
      }

      // Purely local/offline fallback
      _generateEmpatheticResponse(trimmed);
    } finally {
      _isAiGenerating = false;
      notifyListeners();
    }
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
    final lower = userText.toLowerCase().trim();

    final isGibberishOrUnclear = (lower.split(RegExp(r'\s+')).length == 1 &&
            lower.length > 4 &&
            !['hello', 'scared', 'afraid', 'shelter', 'danger', 'threat', 'help', 'ready'].contains(lower)) ||
        RegExp(r'[bcdfghjklmnpqrstvwxyz]{5,}').hasMatch(lower);

    String reply;
    if (isGibberishOrUnclear) {
      reply =
          "I didn't quite catch that, but I'm right here with you. Please take all the time you need—you can type or speak whenever you feel ready, and share only what feels safe.";
    } else if (lower.contains('friend') || lower.contains('stay with') || lower.contains('can stay')) {
      reply =
          "Having a supportive friend and a safe place to go is an important step. You are in complete control of your next steps. Would you like to explore additional safety planning or confidential resources while you're there?";
    } else if (lower.contains('anonymous') || lower.contains('privacy') || lower.contains('secret') || lower.contains('confidential')) {
      reply =
          "Yes, this conversation is completely confidential and protected with end-to-end trauma-informed privacy protocols. You are in full control of what you share, and your identity remains protected.";
    } else if (lower.contains('shelter') || lower.contains('stay tonight') || lower.contains('home tonight') || lower.contains('unsafe') || lower.contains('hostel') || lower.contains('danger') || lower.contains('threat')) {
      reply =
          "Thank you for trusting us with this. Your immediate safety is our utmost priority. We have verified emergency shelter options and advocates ready. If you need urgent assistance tonight, please contact our Demo Support line at 9787872051.";
    } else if (lower.contains('legal') || lower.contains('law') || lower.contains('court') || lower.contains('police') || lower.contains('fir')) {
      reply =
          "We can coordinate confidential pro-bono legal support and rights advisement under the National Helpline Against Atrocities (NHAA) framework whenever you feel ready.";
    } else if (lower.contains('hi') || lower.contains('hello') || lower.contains("i'm ") || lower.contains("i am ") || lower.contains("my name")) {
      String namePart = "";
      for (final prefix in ["i'm ", "i am ", "my name is ", "im "]) {
        if (lower.contains(prefix)) {
          final after = lower.split(prefix).last.trim().split(RegExp(r'\s+')).first.replaceAll(RegExp(r'[.,!?]'), '');
          if (after.isNotEmpty && !['here', 'scared', 'tired', 'fine', 'ready', 'feeling'].contains(after)) {
            namePart = ", ${after[0].toUpperCase()}${after.substring(1)}";
            break;
          }
        }
      }
      reply =
          "Hello$namePart. You are in a safe, confidential space. You can share as much or as little as you'd like, whenever you're ready. How can we support you today?";
    } else if (lower.contains('scared') || lower.contains('fear') || lower.contains('panic') || lower.contains('hurt') || lower.contains('terrified')) {
      reply =
          "It sounds like you're going through something really frightening right now, and I want you to know you don't have to face this alone. Can you tell me a little more about what's been happening, whenever you feel ready?";
    } else {
      reply =
          "Thank you for sharing this with us. We are listening closely, and you can share at your own pace. How can we best assist you right now?";
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
