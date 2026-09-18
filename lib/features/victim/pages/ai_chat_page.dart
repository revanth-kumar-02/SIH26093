import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:record/record.dart';
import '../../../../core/constants/app_strings.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/app_state_service.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/audio_helper.dart';

enum ChatInputMode { text, voice }

enum VoiceInteractionState {
  idle,
  recording,
  paused,
  processingAudio,
  transcribing,
  transcriptReady,
  sendingMessage,
  aiGenerating,
  completed,
  error,
}

/// Screen 6: AI Chat with Voice Interaction & AI Typing Indicator.
class AiChatPage extends StatefulWidget {
  const AiChatPage({super.key});

  @override
  State<AiChatPage> createState() => _AiChatPageState();
}

class _AiChatPageState extends State<AiChatPage> with TickerProviderStateMixin {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AudioRecorder _audioRecorder = AudioRecorder();

  ChatInputMode _chatMode = ChatInputMode.text;
  VoiceInteractionState _voiceState = VoiceInteractionState.idle;
  Timer? _timer;
  int _seconds = 0;
  String? _voiceErrorMessage;

  late final AnimationController _pulseController;

  static const List<String> _promptSuggestions = [
    'I have a friend I can stay with',
    'I need safe shelter tonight',
    'Report anonymously',
    'I need legal advice',
  ];

  @override
  void initState() {
    super.initState();
    AppStateService.instance.addListener(_onStateChanged);
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);
  }

  void _onStateChanged() {
    if (mounted) {
      setState(() {});
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  void dispose() {
    AppStateService.instance.removeListener(_onStateChanged);
    _pulseController.dispose();
    _timer?.cancel();
    _audioRecorder.dispose();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage([String? presetText]) {
    final text = presetText ?? _textController.text.trim();
    if (text.isEmpty) return;
    AppStateService.instance.sendUserMessage(text, inputSource: 'text');
    if (presetText == null) _textController.clear();
    _scrollToBottom();
  }

  Future<void> _startRecording() async {
    final hasPermission = await _audioRecorder.hasPermission();
    if (!hasPermission) {
      if (mounted) _showPermissionDialog();
      return;
    }
    try {
      setState(() {
        _voiceErrorMessage = null;
        _seconds = 0;
        _voiceState = VoiceInteractionState.recording;
      });
      final filePath = await getAudioTempPath();
      await _audioRecorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000,
          numChannels: 1,
        ),
        path: filePath,
      );
      _startTimer();
    } catch (e) {
      setState(() {
        _voiceState = VoiceInteractionState.error;
        _voiceErrorMessage = 'Microphone is unavailable. Please check permissions or type below.';
      });
    }
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_voiceState == VoiceInteractionState.recording && mounted) {
        setState(() => _seconds++);
      }
    });
  }

  Future<void> _togglePauseRecording() async {
    if (_voiceState == VoiceInteractionState.recording) {
      await _audioRecorder.pause();
      setState(() => _voiceState = VoiceInteractionState.paused);
    } else if (_voiceState == VoiceInteractionState.paused) {
      await _audioRecorder.resume();
      setState(() => _voiceState = VoiceInteractionState.recording);
    }
  }

  Future<void> _stopAndCommitVoice() async {
    if (_voiceState != VoiceInteractionState.recording && _voiceState != VoiceInteractionState.paused) {
      return;
    }
    _timer?.cancel();
    setState(() {
      _voiceState = VoiceInteractionState.processingAudio;
      _voiceErrorMessage = null;
    });
    try {
      final path = await _audioRecorder.stop();
      final List<int>? audioBytes = path != null && path.isNotEmpty
          ? await readAudioBytesAndDelete(path)
          : null;
      if (audioBytes != null && audioBytes.isNotEmpty) {
        setState(() {
          _voiceState = VoiceInteractionState.transcribing;
        });
        final result = await AppStateService.instance.transcribeAudioBytes(
          audioBytes: audioBytes,
          filename: 'voice_intake.wav',
        );
        final transcript = result.text.trim();
        if (transcript.isNotEmpty) {
          setState(() {
            _voiceState = VoiceInteractionState.sendingMessage;
          });
          await AppStateService.instance.commitTranscriptToChat(transcript);
          if (mounted) {
            setState(() {
              _voiceState = VoiceInteractionState.completed;
              _seconds = 0;
            });
            _scrollToBottom();
          }
        } else {
          setState(() {
            _voiceState = VoiceInteractionState.error;
            _voiceErrorMessage = 'We could not detect clear speech. Please speak closer to the mic or type.';
          });
        }
      } else {
        setState(() {
          _voiceState = VoiceInteractionState.error;
          _voiceErrorMessage = 'No audio was recorded. Please try speaking again.';
        });
      }
    } catch (e) {
      setState(() {
        _voiceState = VoiceInteractionState.error;
        _voiceErrorMessage = 'Transcription service unavailable. You can type your message anytime.';
      });
    }
  }

  Future<void> _cancelRecording() async {
    _timer?.cancel();
    try {
      if (await _audioRecorder.isRecording()) {
        await _audioRecorder.stop();
      }
    } catch (_) {}
    setState(() {
      _seconds = 0;
      _voiceState = VoiceInteractionState.idle;
      _voiceErrorMessage = null;
    });
  }

  void _showPermissionDialog() {
    showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        title: const Row(
          children: [
            Icon(Icons.mic, color: AppColors.primary, size: 24),
            SizedBox(width: 8),
            Text('Microphone Access', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600, color: AppColors.onSurface)),
          ],
        ),
        content: const Text(
          'To listen gently and accurately transcribe your words using AI speech recognition, TrueVoice Guide needs microphone access.',
          style: TextStyle(fontSize: 13.5, height: 1.5, color: AppColors.onSurfaceVariant),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel', style: TextStyle(color: AppColors.onSurfaceVariant)),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.primary),
            onPressed: () {
              Navigator.of(ctx).pop();
              _startRecording();
            },
            child: const Text('Allow & Start'),
          ),
        ],
      ),
    );
  }

  void _showBreathingModal() {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 10),
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.secondaryContainer.withValues(alpha: 0.6),
              ),
              child: const Icon(Icons.self_improvement, size: 40, color: AppColors.primary),
            ),
            const SizedBox(height: 20),
            const Text(
              'Grounding Moment',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.onSurface),
            ),
            const SizedBox(height: 8),
            const Text(
              'Inhale gently for 4 seconds...\\nHold for 4 seconds...\\nExhale slowly for 4 seconds.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, height: 1.6, color: AppColors.onSurfaceVariant),
            ),
            const SizedBox(height: 20),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('I Feel Ready to Continue'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final appState = AppStateService.instance;
    final messages = appState.messages;
    final isAiGenerating = appState.isAiGenerating;
    final hasDivider = messages.length > 2;
    final extraItems = (hasDivider ? 1 : 0) + (isAiGenerating ? 1 : 0);
    final totalCount = messages.length + extraItems;

    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.onSurface),
          onPressed: () => context.go(RoutePaths.home),
        ),
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                color: AppColors.secondaryContainer,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.eco, size: 18, color: AppColors.primary),
            ),
            const SizedBox(width: 10),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'TrueVoice Guide',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.onSurface),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    'Encrypted & confidential',
                    style: TextStyle(fontSize: 11, color: AppColors.secondary),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Restart chat',
            icon: const Icon(Icons.refresh, size: 20, color: AppColors.secondary),
            onPressed: () {
              AppStateService.instance.clearChat();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Chat restarted fresh.'),
                  duration: Duration(seconds: 1),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
          TextButton.icon(
            onPressed: () {
              AppStateService.instance.advanceAssessmentStep(2);
              context.go(RoutePaths.assessmentStatus);
            },
            icon: const Icon(Icons.check_circle_outline, size: 16, color: AppColors.primary),
            label: const Text(
              'Done',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.primary),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Column(
              children: [
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.lock, size: 13, color: AppColors.secondary),
                      SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          'Your words are safe. Take all the time you need.',
                          style: TextStyle(fontSize: 11.5, color: AppColors.secondary, fontWeight: FontWeight.w500),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  padding: const EdgeInsets.all(3),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: InkWell(
                          onTap: () => setState(() => _chatMode = ChatInputMode.text),
                          borderRadius: BorderRadius.circular(9),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            padding: const EdgeInsets.symmetric(vertical: 7),
                            decoration: BoxDecoration(
                              color: _chatMode == ChatInputMode.text ? AppColors.surfaceContainerLowest : Colors.transparent,
                              borderRadius: BorderRadius.circular(9),
                              boxShadow: _chatMode == ChatInputMode.text
                                  ? [
                                      BoxShadow(
                                        color: Colors.black.withValues(alpha: 0.04),
                                        blurRadius: 4,
                                        offset: const Offset(0, 1),
                                      )
                                    ]
                                  : null,
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.chat_bubble_outline,
                                  size: 15,
                                  color: _chatMode == ChatInputMode.text ? AppColors.primary : AppColors.onSurfaceVariant,
                                ),
                                const SizedBox(width: 6),
                                Flexible(
                                  child: Text(
                                    'Text Chat',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: _chatMode == ChatInputMode.text ? FontWeight.w600 : FontWeight.w500,
                                      color: _chatMode == ChatInputMode.text ? AppColors.onSurface : AppColors.onSurfaceVariant,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      Expanded(
                        child: InkWell(
                          onTap: () => setState(() => _chatMode = ChatInputMode.voice),
                          borderRadius: BorderRadius.circular(9),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            padding: const EdgeInsets.symmetric(vertical: 7),
                            decoration: BoxDecoration(
                              color: _chatMode == ChatInputMode.voice ? AppColors.surfaceContainerLowest : Colors.transparent,
                              borderRadius: BorderRadius.circular(9),
                              boxShadow: _chatMode == ChatInputMode.voice
                                  ? [
                                      BoxShadow(
                                        color: Colors.black.withValues(alpha: 0.04),
                                        blurRadius: 4,
                                        offset: const Offset(0, 1),
                                      )
                                    ]
                                  : null,
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  Icons.mic,
                                  size: 15,
                                  color: _chatMode == ChatInputMode.voice ? AppColors.primary : AppColors.onSurfaceVariant,
                                ),
                                const SizedBox(width: 6),
                                Flexible(
                                  child: Text(
                                    'Voice Mode',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: _chatMode == ChatInputMode.voice ? FontWeight.w600 : FontWeight.w500,
                                      color: _chatMode == ChatInputMode.voice ? AppColors.onSurface : AppColors.onSurfaceVariant,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    itemCount: totalCount,
                    itemBuilder: (context, index) {
                      if (hasDivider && index == 2) {
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: Center(
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                              decoration: BoxDecoration(
                                color: AppColors.surfaceContainerHigh,
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.favorite, size: 14, color: AppColors.primary),
                                  SizedBox(width: 6),
                                  Flexible(
                                    child: Text(
                                      "Remember: You don't have to answer anything you aren't ready for.",
                                      style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500, color: AppColors.onSurfaceVariant),
                                      textAlign: TextAlign.center,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      }
                      final isTypingBubbleItem = isAiGenerating && index == totalCount - 1;
                      if (isTypingBubbleItem) {
                        return const _AiTypingBubble();
                      }
                      final msgIndex = (hasDivider && index > 2) ? index - 1 : index;
                      final message = messages[msgIndex];
                      final isError = message.id.startsWith('asst-err');

                      if (message.isAssistant) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 28,
                                height: 28,
                                decoration: BoxDecoration(
                                  color: isError ? AppColors.errorContainer : AppColors.surfaceContainerHighest,
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  isError ? Icons.error_outline : Icons.eco,
                                  size: 16,
                                  color: isError ? AppColors.error : AppColors.primary,
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(14),
                                      decoration: BoxDecoration(
                                        color: isError ? AppColors.surfaceContainerLow : AppColors.surfaceContainerLowest,
                                        borderRadius: const BorderRadius.only(
                                          topRight: Radius.circular(16),
                                          bottomLeft: Radius.circular(16),
                                          bottomRight: Radius.circular(16),
                                          topLeft: Radius.circular(4),
                                        ),
                                        border: isError ? Border.all(color: AppColors.error.withValues(alpha: 0.3)) : null,
                                        boxShadow: [
                                          BoxShadow(
                                            color: Colors.black.withValues(alpha: 0.02),
                                            blurRadius: 6,
                                            offset: const Offset(0, 2),
                                          ),
                                        ],
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            message.text,
                                            style: TextStyle(
                                              fontSize: 14,
                                              height: 1.5,
                                              color: isError ? AppColors.error : AppColors.onSurface,
                                            ),
                                          ),
                                          if (isError) ...[
                                            const SizedBox(height: 8),
                                            OutlinedButton.icon(
                                              style: OutlinedButton.styleFrom(
                                                foregroundColor: AppColors.primary,
                                                side: const BorderSide(color: AppColors.primary, width: 1),
                                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                                                visualDensity: VisualDensity.compact,
                                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                                              ),
                                              onPressed: () => AppStateService.instance.retryLastMessage(),
                                              icon: const Icon(Icons.refresh, size: 14),
                                              label: const Text('Retry message', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                            ),
                                          ],
                                        ],
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'TrueVoice Guide • \${message.timestamp}',
                                      style: const TextStyle(fontSize: 11, color: AppColors.onSurfaceVariant),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      } else {
                        final isVoiceSource = message.inputSource == 'voice';
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                              Flexible(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(14),
                                      decoration: const BoxDecoration(
                                        color: AppColors.secondaryContainer,
                                        borderRadius: BorderRadius.only(
                                          topLeft: Radius.circular(16),
                                          bottomLeft: Radius.circular(16),
                                          bottomRight: Radius.circular(16),
                                          topRight: Radius.circular(4),
                                        ),
                                      ),
                                      child: Text(
                                        message.text,
                                        style: const TextStyle(
                                          fontSize: 14,
                                          height: 1.5,
                                          color: AppColors.onSecondaryContainer,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          isVoiceSource ? 'Spoken by you' : 'Shared by you',
                                          style: const TextStyle(fontSize: 11, color: AppColors.onSurfaceVariant),
                                        ),
                                        const SizedBox(width: 4),
                                        Icon(
                                          isVoiceSource ? Icons.mic_none : Icons.done_all,
                                          size: 14,
                                          color: AppColors.primary,
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      }
                    },
                  ),
                ),
                if (_chatMode == ChatInputMode.text)
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Row(
                      children: _promptSuggestions.map((prompt) {
                        return Padding(
                          padding: const EdgeInsets.only(right: 8),
                          child: ActionChip(
                            backgroundColor: AppColors.surfaceContainerLow,
                            visualDensity: VisualDensity.compact,
                            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(999),
                              side: BorderSide(
                                color: AppColors.outlineVariant.withValues(alpha: 0.3),
                              ),
                            ),
                            label: Text(
                              prompt,
                              style: const TextStyle(
                                fontSize: 12,
                                color: AppColors.onSurface,
                                fontWeight: FontWeight.w400,
                              ),
                            ),
                            onPressed: isAiGenerating ? null : () => _sendMessage(prompt),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                const SizedBox(height: 8),
                _chatMode == ChatInputMode.text ? _buildTextInputSection() : _buildVoiceInputSection(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextInputSection() {
    final isGenerating = AppStateService.instance.isAiGenerating;
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          TextField(
            controller: _textController,
            maxLines: 3,
            minLines: 1,
            style: const TextStyle(
              fontSize: 14.5,
              color: AppColors.onSurface,
              fontWeight: FontWeight.w400,
              height: 1.45,
            ),
            cursorColor: AppColors.primary,
            cursorWidth: 2.0,
            decoration: InputDecoration(
              hintText: AppStrings.tr('chat_hint'),
              hintStyle: TextStyle(
                fontSize: 13.5,
                color: AppColors.onSurfaceVariant.withValues(alpha: 0.75),
                fontWeight: FontWeight.w400,
              ),
              border: InputBorder.none,
              fillColor: AppColors.surfaceContainerLow,
              filled: true,
              contentPadding: const EdgeInsets.all(12),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: AppColors.primary, width: 1.2),
              ),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.mic_none, color: AppColors.primary, size: 20),
                    onPressed: () => setState(() => _chatMode = ChatInputMode.voice),
                    tooltip: 'Switch to Voice Mode',
                  ),
                  InkWell(
                    onTap: _showBreathingModal,
                    borderRadius: BorderRadius.circular(999),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(999),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.self_improvement, size: 15, color: AppColors.primary),
                          const SizedBox(width: 4),
                          Text(
                            AppStrings.tr('breathe'),
                            style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500, color: AppColors.onSurfaceVariant),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              FilledButton(
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  minimumSize: const Size(0, 44),
                ),
                onPressed: isGenerating ? null : () => _sendMessage(),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(AppStrings.tr('send'), style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                    const SizedBox(width: 4),
                    const Icon(Icons.send, size: 14),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildVoiceInputSection() {
    final isRecording = _voiceState == VoiceInteractionState.recording;
    final isPaused = _voiceState == VoiceInteractionState.paused;
    final isProcessing = _voiceState == VoiceInteractionState.processingAudio ||
        _voiceState == VoiceInteractionState.transcribing ||
        _voiceState == VoiceInteractionState.sendingMessage;

    String statusText;
    switch (_voiceState) {
      case VoiceInteractionState.recording:
        final m = (_seconds ~/ 60).toString().padLeft(2, '0');
        final s = (_seconds % 60).toString().padLeft(2, '0');
        statusText = 'Recording... $m:$s';
        break;
      case VoiceInteractionState.paused:
        statusText = 'Recording paused. Tap resume when ready.';
        break;
      case VoiceInteractionState.processingAudio:
        statusText = 'Processing voice audio...';
        break;
      case VoiceInteractionState.transcribing:
        statusText = 'Transcribing with IndicConformer ASR...';
        break;
      case VoiceInteractionState.sendingMessage:
        statusText = 'Committing voice transcript to chat...';
        break;
      case VoiceInteractionState.aiGenerating:
        statusText = 'TrueVoice Guide thinking...';
        break;
      case VoiceInteractionState.completed:
        statusText = 'Voice transcript committed safely!';
        break;
      case VoiceInteractionState.error:
        statusText = _voiceErrorMessage ?? 'Recording issue encountered.';
        break;
      case VoiceInteractionState.idle:
      default:
        statusText = 'Tap the microphone to speak gently.';
        break;
    }

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (isRecording) ...[
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) => Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppColors.error.withValues(alpha: 0.5 + (_pulseController.value * 0.5)),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
              ] else if (isProcessing) ...[
                const SizedBox(
                  width: 12,
                  height: 12,
                  child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                ),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: Text(
                  statusText,
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: isRecording ? FontWeight.w600 : FontWeight.w500,
                    color: _voiceState == VoiceInteractionState.error
                        ? AppColors.error
                        : (isRecording ? AppColors.error : AppColors.onSurfaceVariant),
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              if (isRecording || isPaused || _voiceState == VoiceInteractionState.completed || _voiceState == VoiceInteractionState.error)
                IconButton(
                  tooltip: 'Cancel recording',
                  style: IconButton.styleFrom(
                    backgroundColor: AppColors.surfaceContainerLow,
                    minimumSize: const Size(44, 44),
                  ),
                  icon: const Icon(Icons.close, size: 20, color: AppColors.onSurfaceVariant),
                  onPressed: isProcessing ? null : _cancelRecording,
                )
              else
                const SizedBox(width: 44),
              GestureDetector(
                onTap: isProcessing
                    ? null
                    : (isRecording
                        ? _stopAndCommitVoice
                        : (isPaused ? _togglePauseRecording : _startRecording)),
                child: AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    final scale = isRecording ? 1.0 + (_pulseController.value * 0.08) : 1.0;
                    return Transform.scale(
                      scale: scale,
                      child: Container(
                        width: 54,
                        height: 54,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: isRecording ? AppColors.error : AppColors.primary,
                          boxShadow: [
                            BoxShadow(
                              color: (isRecording ? AppColors.error : AppColors.primary).withValues(alpha: 0.3),
                              blurRadius: 10,
                              offset: const Offset(0, 3),
                            ),
                          ],
                        ),
                        child: Icon(
                          isRecording ? Icons.stop : Icons.mic,
                          color: Colors.white,
                          size: 26,
                        ),
                      ),
                    );
                  },
                ),
              ),
              if (isRecording || isPaused)
                IconButton(
                  tooltip: isRecording ? 'Pause' : 'Resume',
                  style: IconButton.styleFrom(
                    backgroundColor: AppColors.surfaceContainerLow,
                    minimumSize: const Size(44, 44),
                  ),
                  icon: Icon(
                    isRecording ? Icons.pause : Icons.play_arrow,
                    size: 20,
                    color: AppColors.primary,
                  ),
                  onPressed: isProcessing ? null : _togglePauseRecording,
                )
              else
                const SizedBox(width: 44),
            ],
          ),
          if (isRecording || isPaused) ...[
            const SizedBox(height: 8),
            TextButton.icon(
              style: TextButton.styleFrom(
                minimumSize: const Size(0, 36),
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              ),
              onPressed: isProcessing ? null : _stopAndCommitVoice,
              icon: const Icon(Icons.check, size: 16, color: AppColors.primary),
              label: const Text(
                'Done & Send to Chat',
                style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600, color: AppColors.primary),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

/// AI Typing Bubble with 3 pulsating dots.
class _AiTypingBubble extends StatefulWidget {
  const _AiTypingBubble();

  @override
  State<_AiTypingBubble> createState() => _AiTypingBubbleState();
}

class _AiTypingBubbleState extends State<_AiTypingBubble> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 28,
            height: 28,
            decoration: const BoxDecoration(
              color: AppColors.surfaceContainerHighest,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.eco, size: 16, color: AppColors.primary),
          ),
          const SizedBox(width: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: AppColors.surfaceContainerLowest,
              borderRadius: const BorderRadius.only(
                topRight: Radius.circular(16),
                bottomLeft: Radius.circular(16),
                bottomRight: Radius.circular(16),
                topLeft: Radius.circular(4),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.02),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: AnimatedBuilder(
              animation: _controller,
              builder: (context, child) {
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(3, (index) {
                    final delay = index * 0.2;
                    final progress = (_controller.value - delay) % 1.0;
                    final wave = (progress < 0.5) ? progress * 2 : (1.0 - progress) * 2;
                    final opacity = 0.35 + (wave * 0.65);
                    final scale = 0.8 + (wave * 0.4);

                    return Padding(
                      padding: EdgeInsets.symmetric(horizontal: index == 1 ? 4.0 : 0.0),
                      child: Transform.scale(
                        scale: scale,
                        child: Opacity(
                          opacity: opacity.clamp(0.2, 1.0),
                          child: Container(
                            width: 7,
                            height: 7,
                            decoration: const BoxDecoration(
                              color: AppColors.primary,
                              shape: BoxShape.circle,
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
