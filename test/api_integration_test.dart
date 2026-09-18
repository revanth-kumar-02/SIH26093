import 'package:flutter_test/flutter_test.dart';
import 'package:nhaa_stress_assessment/core/network/api_config.dart';
import 'package:nhaa_stress_assessment/core/network/api_exceptions.dart';
import 'package:nhaa_stress_assessment/features/victim/data/models/api_models.dart';
import 'package:nhaa_stress_assessment/core/services/app_state_service.dart';
import 'package:nhaa_stress_assessment/shared/models/chat_message.dart';

void main() {
  group('API Models Unit Tests', () {
    test('BackendSession parses from JSON accurately', () {
      final json = {
        'session_id': 'sess-1234-abcd',
        'language': 'en',
        'decoder': 'ctc',
        'status': 'active',
        'created_at': '2026-09-16T13:00:00Z',
      };
      final session = BackendSession.fromJson(json);
      expect(session.sessionId, 'sess-1234-abcd');
      expect(session.language, 'en');
      expect(session.status, 'active');
      expect(session.createdAt, '2026-09-16T13:00:00Z');
    });

    test('BackendChatMessage parses from JSON accurately', () {
      final json = {
        'message_id': 'msg-9876',
        'response': 'Take your time. You can share what happened in your own words.',
        'status': 'received',
        'timestamp': '2026-09-16T13:01:00Z',
      };
      final message = BackendChatMessage.fromJson(json);
      expect(message.messageId, 'msg-9876');
      expect(message.response, contains('Take your time'));
      expect(message.status, 'received');
      expect(message.timestamp, '2026-09-16T13:01:00Z');
    });

    test('BackendAssessment parses placeholder contract accurately', () {
      final json = {
        'session_id': 'sess-1234',
        'status': 'pending_review',
        'assessment': {
          'risk_level': 'not_available',
          'svi': null,
          'indicators': <dynamic>[],
        },
      };
      final assessment = BackendAssessment.fromJson(json);
      expect(assessment.sessionId, 'sess-1234');
      expect(assessment.status, 'pending_review');
      expect(assessment.riskLevel, 'not_available');
      expect(assessment.svi, isNull);
      expect(assessment.indicators, isEmpty);
    });

    test('BackendTranscription parses transcription response accurately', () {
      final json = {
        'session_id': 'sess-5678',
        'transcript': 'I need immediate safe shelter tonight.',
        'language': 'en',
        'decoder': 'ctc',
        'status': 'completed',
        'timestamp': '2026-09-16T13:02:00Z',
        'speech_emotion': {
          'emotion': 'fearful',
          'probabilities': {
            'angry': 0.05,
            'calm': 0.10,
            'disgust': 0.02,
            'fearful': 0.65,
            'happy': 0.01,
            'sad': 0.12,
            'surprised': 0.05,
          },
          'model_version': 'Dpngtm/wav2vec2-emotion-recognition',
          'duration_ms': 12.4,
          'device': 'cpu',
        },
      };
      final transcription = BackendTranscription.fromJson(json);
      expect(transcription.sessionId, 'sess-5678');
      expect(transcription.text, 'I need immediate safe shelter tonight.');
      expect(transcription.transcript, 'I need immediate safe shelter tonight.');
      expect(transcription.language, 'en');
      expect(transcription.decoder, 'ctc');
      expect(transcription.status, 'completed');
      expect(transcription.timestamp, '2026-09-16T13:02:00Z');
      expect(transcription.speechEmotion, isNotNull);
      expect(transcription.speechEmotion?.emotion, 'fearful');
      expect(transcription.speechEmotion?.probabilities['fearful'], 0.65);
    });

    test('SpeechEmotionResult parses Wav2Vec2 7-class distribution accurately', () {
      final json = {
        'emotion': 'calm',
        'probabilities': {
          'angry': 0.02,
          'calm': 0.78,
          'disgust': 0.01,
          'fearful': 0.08,
          'happy': 0.03,
          'sad': 0.05,
          'surprised': 0.03,
        },
        'model_version': 'Dpngtm/wav2vec2-emotion-recognition',
        'duration_ms': 15.2,
        'device': 'cpu',
      };
      final result = SpeechEmotionResult.fromJson(json);
      expect(result.emotion, 'calm');
      expect(result.probabilities['calm'], 0.78);
      expect(result.probabilities['angry'], 0.02);
      expect(result.probabilities.length, 7);
      expect(result.modelVersion, 'Dpngtm/wav2vec2-emotion-recognition');
      expect(result.durationMs, 15.2);
    });

    test('TextEmotionResult parses GoEmotions taxonomy accurately', () {
      final json = {
        'top_emotion': 'fear',
        'emotions': [
          {'label': 'fear', 'score': 0.85},
          {'label': 'nervousness', 'score': 0.62},
          {'label': 'sadness', 'score': 0.20},
          {'label': 'caring', 'score': 0.10},
          {'label': 'neutral', 'score': 0.05},
        ],
        'model_version': 'SamLowe/roberta-base-go_emotions',
        'duration_ms': 4.1,
        'device': 'cpu',
      };
      final result = TextEmotionResult.fromJson(json);
      expect(result.topEmotion, 'fear');
      expect(result.emotions.length, 5);
      expect(result.emotions.first.label, 'fear');
      expect(result.emotions.first.score, 0.85);
      expect(result.modelVersion, 'SamLowe/roberta-base-go_emotions');
      expect(result.durationMs, 4.1);
    });
  });

  group('API Config & Network Exceptions', () {
    test('ApiConfig produces valid endpoints including transcribe and emotion', () {
      expect(ApiConfig.sessionsUrl, contains('/api/v1/sessions'));
      expect(
        ApiConfig.sessionMessagesUrl('sess-1'),
        contains('/api/v1/sessions/sess-1/messages'),
      );
      expect(
        ApiConfig.sessionAssessmentUrl('sess-1'),
        contains('/api/v1/sessions/sess-1/assessment'),
      );
      expect(
        ApiConfig.sessionTranscribeUrl('sess-1'),
        contains('/api/v1/sessions/sess-1/transcribe'),
      );
      expect(
        ApiConfig.sessionAnalyzeTextUrl('sess-1'),
        contains('/api/v1/sessions/sess-1/analyze/text'),
      );
      expect(
        ApiConfig.sessionAnalyzeAudioUrl('sess-1'),
        contains('/api/v1/sessions/sess-1/analyze/audio'),
      );
    });

    test('Network exceptions expose calm user messages without technical stack traces', () {
      const connEx = NetworkConnectionException();
      expect(connEx.userMessage, contains('connect'));

      const serverEx = ServerErrorException(statusCode: 500);
      expect(serverEx.userMessage, contains('currently unavailable'));

      const timeoutEx = RequestTimeoutException();
      expect(timeoutEx.userMessage, contains('timed out'));
    });
  });

  group('Conversation Model & Voice Bridge', () {
    test('ChatMessage supports both text and voice input sources', () {
      const textMsg = ChatMessage(
        id: 'msg-1',
        isAssistant: false,
        text: 'I need advice on legal aid',
        timestamp: '10:30 AM',
        inputSource: 'text',
      );
      expect(textMsg.inputSource, 'text');
      expect(textMsg.isAssistant, isFalse);

      const voiceMsg = ChatMessage(
        id: 'msg-2',
        isAssistant: false,
        text: 'I am safe for now but need help tomorrow',
        timestamp: '10:32 AM',
        inputSource: 'voice',
      );
      expect(voiceMsg.inputSource, 'voice');
      expect(voiceMsg.isAssistant, isFalse);
    });

    test('AppStateService correctly maps language codes', () {
      final appState = AppStateService.instance;
      expect(appState.currentLanguageCode, 'en');

      appState.setLanguage('Hindi');
      expect(appState.currentLanguageCode, 'hi');

      appState.setLanguage('Tamil');
      expect(appState.currentLanguageCode, 'ta');

      appState.setLanguage('Telugu');
      expect(appState.currentLanguageCode, 'te');

      appState.setLanguage('Kannada');
      expect(appState.currentLanguageCode, 'kn');

      appState.setLanguage('Malayalam');
      expect(appState.currentLanguageCode, 'ml');

      appState.setLanguage('English');
      expect(appState.currentLanguageCode, 'en');
    });

    test('Committing transcript to chat appends message with voice source', () async {
      final appState = AppStateService.instance;
      await appState.commitTranscriptToChat('I am looking for emergency shelter assistance');
      expect(appState.messages.any((m) => m.inputSource == 'voice' && m.text.contains('emergency shelter')), isTrue);

      final userVoiceMessage = appState.messages.firstWhere((m) => m.inputSource == 'voice');
      expect(userVoiceMessage.text, 'I am looking for emergency shelter assistance');
      expect(userVoiceMessage.isAssistant, isFalse);
      expect(userVoiceMessage.inputSource, 'voice');
    });

    test('AppStateService manages AI generating state and retry accurately', () async {
      final appState = AppStateService.instance;
      expect(appState.isAiGenerating, isFalse);

      final sendFuture = appState.sendUserMessage('Testing AI typing state');
      expect(appState.isAiGenerating, isTrue);
      await sendFuture;
      expect(appState.isAiGenerating, isFalse);
    });
  });
}