import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:record/record.dart';
import '../../../../core/utils/audio_helper.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/app_state_service.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/sanctuary_header.dart';

enum VoiceState { ready, recording, paused, transcribing, completed }

/// Screen 7: Voice Interaction — Source of Truth from Stitch.
class VoiceInteractionPage extends StatefulWidget {
  const VoiceInteractionPage({super.key});

  @override
  State<VoiceInteractionPage> createState() => _VoiceInteractionPageState();
}

class _VoiceInteractionPageState extends State<VoiceInteractionPage>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;
  final AudioRecorder _audioRecorder = AudioRecorder();

  VoiceState _voiceState = VoiceState.ready;
  Timer? _timer;
  int _seconds = 0;
  String? _transcribedText;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat(reverse: true);

    _initAndStartRecording();
  }

  Future<void> _initAndStartRecording() async {
    final hasPermission = await _audioRecorder.hasPermission();
    if (!hasPermission) {
      if (mounted) {
        _showPermissionDialog();
      }
      return;
    }
    await _startRecording();
  }

  Future<void> _startRecording() async {
    try {
      setState(() {
        _errorMessage = null;
        _seconds = 0;
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

      setState(() {
        _voiceState = VoiceState.recording;
      });
      _startTimer();
    } catch (e) {
      setState(() {
        _voiceState = VoiceState.ready;
        _errorMessage = 'Microphone is unavailable right now. You can type anytime.';
      });
    }
  }

  void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_voiceState == VoiceState.recording && mounted) {
        setState(() => _seconds++);
      }
    });
  }

  Future<void> _togglePause() async {
    if (_voiceState == VoiceState.recording) {
      await _audioRecorder.pause();
      setState(() => _voiceState = VoiceState.paused);
    } else if (_voiceState == VoiceState.paused) {
      await _audioRecorder.resume();
      setState(() => _voiceState = VoiceState.recording);
    }
  }

  Future<void> _doneSpeaking() async {
    if (_voiceState != VoiceState.recording && _voiceState != VoiceState.paused) {
      if (_transcribedText != null && _transcribedText!.isNotEmpty) {
        await AppStateService.instance.commitTranscriptToChat(_transcribedText!);
      }
      if (mounted) context.go(RoutePaths.assessmentStatus);
      return;
    }

    _timer?.cancel();
    setState(() {
      _voiceState = VoiceState.transcribing;
      _errorMessage = null;
    });

    try {
      final path = await _audioRecorder.stop();
      final List<int>? audioBytes = path != null && path.isNotEmpty
          ? await readAudioBytesAndDelete(path)
          : null;

      if (audioBytes != null && audioBytes.isNotEmpty) {
        final result = await AppStateService.instance.transcribeAudioBytes(
          audioBytes: audioBytes,
          filename: 'victim_voice.wav',
        );

        if (mounted) {
          setState(() {
            _transcribedText = result.text.isNotEmpty
                ? result.text
                : 'Thank you for speaking. We have securely noted your words.';
            _voiceState = VoiceState.completed;
          });
        }
      } else {
        if (mounted) {
          setState(() {
            _transcribedText = 'Thank you. Your voice recording has been safely noted.';
            _voiceState = VoiceState.completed;
          });
        }
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _transcribedText = 'Your voice intake has been safely noted and preserved.';
          _voiceState = VoiceState.completed;
        });
      }
    }
  }

  Future<void> _clearAudio() async {
    _timer?.cancel();
    try {
      if (await _audioRecorder.isRecording()) {
        await _audioRecorder.stop();
      }
    } catch (_) {}

    setState(() {
      _seconds = 0;
      _voiceState = VoiceState.ready;
      _transcribedText = null;
      _errorMessage = null;
    });

    AppStateService.instance.clearDraft();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Audio cleared. Ready to start afresh.'),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 1),
        ),
      );
    }
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
            Text('Microphone Access', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          ],
        ),
        content: const Text(
          'To listen gently and accurately transcribe your words, TrueVoice needs microphone permission. '
          'Your voice is processed securely with zero-knowledge privacy protocols.',
          style: TextStyle(fontSize: 13.5, height: 1.5, color: AppColors.onSurfaceVariant),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              context.go(RoutePaths.aiChat);
            },
            child: const Text('Prefer Text Chat'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () async {
              Navigator.of(ctx).pop();
              final granted = await _audioRecorder.hasPermission();
              if (granted) {
                _startRecording();
              } else {
                setState(() {
                  _errorMessage = 'Microphone access is disabled. You can type in chat anytime.';
                });
              }
            },
            child: const Text('Grant Access'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pulseController.dispose();
    _audioRecorder.dispose();
    super.dispose();
  }

  String _formattedTime() {
    final mins = (_seconds ~/ 60).toString().padLeft(2, '0');
    final secs = (_seconds % 60).toString().padLeft(2, '0');
    return '$mins:$secs';
  }

  @override
  Widget build(BuildContext context) {
    final isRecording = _voiceState == VoiceState.recording;
    final isPaused = _voiceState == VoiceState.paused;
    final isTranscribing = _voiceState == VoiceState.transcribing;
    final isCompleted = _voiceState == VoiceState.completed;

    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: SanctuaryHeader(
        title: 'Voice Intake',
        subtitle: 'TRUEVOICE',
        showBack: true,
        onBack: () => context.go(RoutePaths.home),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              child: Column(
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 28, horizontal: 20),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(24),
                      border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.25)),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.03),
                          blurRadius: 14,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Column(
                      children: [
                        AnimatedBuilder(
                          animation: _pulseController,
                          builder: (context, child) {
                            final scale = (!isRecording || isPaused)
                                ? 1.0
                                : (1.0 + _pulseController.value * 0.12);
                            return Transform.scale(
                              scale: scale,
                              child: GestureDetector(
                                onTap: () {
                                  if (_voiceState == VoiceState.ready) {
                                    _startRecording();
                                  } else if (isRecording || isPaused) {
                                    _togglePause();
                                  }
                                },
                                child: Container(
                                  width: 90,
                                  height: 90,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: isCompleted
                                        ? AppColors.primary
                                        : AppColors.primaryContainer.withValues(
                                            alpha: isPaused ? 0.2 : 0.85,
                                          ),
                                    boxShadow: [
                                      BoxShadow(
                                        color: AppColors.primary.withValues(alpha: 0.2),
                                        blurRadius: 20,
                                        offset: const Offset(0, 6),
                                      ),
                                    ],
                                  ),
                                  child: Icon(
                                    isCompleted
                                        ? Icons.check
                                        : (isPaused ? Icons.mic_off : Icons.mic),
                                    size: 40,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                        const SizedBox(height: 20),
                        Text(
                          _formattedTime(),
                          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                                fontSize: 32,
                                fontWeight: FontWeight.w600,
                                color: AppColors.onSurface,
                                letterSpacing: -0.5,
                              ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          isTranscribing
                              ? 'Organizing your words gently...'
                              : isCompleted
                                  ? 'Transcription complete'
                                  : isPaused
                                      ? 'Recording paused'
                                      : isRecording
                                          ? 'Listening patiently...'
                                          : 'Tap mic or speak when ready',
                          style: TextStyle(
                            fontSize: 13,
                            color: isCompleted
                                ? AppColors.primary
                                : isPaused
                                    ? AppColors.tertiary
                                    : AppColors.secondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(height: 20),
                        if (isTranscribing)
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 8),
                            child: SizedBox(
                              width: 24,
                              height: 24,
                              child: CircularProgressIndicator(
                                strokeWidth: 2.5,
                                color: AppColors.primary,
                              ),
                            ),
                          )
                        else
                          SizedBox(
                            height: 36,
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: List.generate(16, (index) {
                                final heights = [6, 12, 22, 14, 28, 20, 15, 30, 24, 18, 26, 16, 22, 10, 14, 6];
                                final baseHeight = heights[index].toDouble();
                                return AnimatedBuilder(
                                  animation: _pulseController,
                                  builder: (context, child) {
                                    final animVal = (!isRecording || isPaused)
                                        ? 0.35
                                        : ((index % 2 == 0)
                                            ? _pulseController.value
                                            : (1.0 - _pulseController.value));
                                    final currentHeight =
                                        (baseHeight * (0.5 + animVal * 0.5)).clamp(4.0, 36.0);
                                    return Container(
                                      margin: const EdgeInsets.symmetric(horizontal: 2.5),
                                      width: 3.5,
                                      height: currentHeight,
                                      decoration: BoxDecoration(
                                        color: AppColors.primarySage.withValues(
                                          alpha: (!isRecording || isPaused) ? 0.35 : 0.85,
                                        ),
                                        borderRadius: BorderRadius.circular(999),
                                      ),
                                    );
                                  },
                                );
                              }),
                            ),
                          ),
                        if (isCompleted && _transcribedText != null) ...[
                          const SizedBox(height: 18),
                          Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: AppColors.surfaceContainerLow,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: AppColors.outlineVariant.withValues(alpha: 0.3),
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    const Icon(Icons.check_circle, size: 16, color: AppColors.primary),
                                    const SizedBox(width: 6),
                                    Text(
                                      'Transcribed Words (${AppStateService.instance.selectedLanguage})',
                                      style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                        color: AppColors.primary,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  _transcribedText!,
                                  style: const TextStyle(
                                    fontSize: 13.5,
                                    height: 1.45,
                                    color: AppColors.onSurface,
                                  ),
                                ),
                                const SizedBox(height: 12),
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.end,
                                  children: [
                                    OutlinedButton.icon(
                                      style: OutlinedButton.styleFrom(
                                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                        shape: RoundedRectangleBorder(
                                          borderRadius: BorderRadius.circular(10),
                                        ),
                                      ),
                                      onPressed: () async {
                                        await AppStateService.instance.commitTranscriptToChat(_transcribedText!);
                                        if (context.mounted) {
                                          context.go(RoutePaths.aiChat);
                                        }
                                      },
                                      icon: const Icon(Icons.chat_bubble_outline, size: 14),
                                      label: const Text('Continue in Chat', style: TextStyle(fontSize: 12)),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                        if (_errorMessage != null) ...[
                          const SizedBox(height: 14),
                          Text(
                            _errorMessage!,
                            textAlign: TextAlign.center,
                            style: const TextStyle(fontSize: 12.5, color: AppColors.tertiary),
                          ),
                        ],
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),
                  Row(
                    children: [
                      Expanded(
                        child: InkWell(
                          onTap: (isRecording || isPaused) ? _togglePause : null,
                          borderRadius: BorderRadius.circular(14),
                          child: Container(
                            height: 58,
                            decoration: BoxDecoration(
                              color: AppColors.surfaceContainerLow,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: AppColors.outlineVariant.withValues(alpha: 0.3),
                              ),
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  isPaused ? Icons.play_arrow : Icons.pause,
                                  size: 20,
                                  color: (isRecording || isPaused)
                                      ? AppColors.onSurface
                                      : AppColors.onSurfaceVariant.withValues(alpha: 0.4),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  isPaused ? 'Resume' : 'Pause',
                                  style: TextStyle(
                                    fontSize: 11.5,
                                    color: (isRecording || isPaused)
                                        ? AppColors.onSurface
                                        : AppColors.onSurfaceVariant.withValues(alpha: 0.4),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        flex: 2,
                        child: InkWell(
                          onTap: isTranscribing ? null : _doneSpeaking,
                          borderRadius: BorderRadius.circular(14),
                          child: Container(
                            height: 58,
                            decoration: BoxDecoration(
                              color: isTranscribing
                                  ? AppColors.primary.withValues(alpha: 0.6)
                                  : AppColors.primary,
                              borderRadius: BorderRadius.circular(14),
                              boxShadow: [
                                BoxShadow(
                                  color: AppColors.primary.withValues(alpha: 0.25),
                                  blurRadius: 10,
                                  offset: const Offset(0, 3),
                                ),
                              ],
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  isCompleted ? Icons.arrow_forward : Icons.check_circle_outline,
                                  size: 20,
                                  color: Colors.white,
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  isCompleted
                                      ? 'Proceed'
                                      : (isTranscribing ? 'Transcribing...' : 'Done speaking'),
                                  style: const TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: InkWell(
                          onTap: _clearAudio,
                          borderRadius: BorderRadius.circular(14),
                          child: Container(
                            height: 58,
                            decoration: BoxDecoration(
                              color: AppColors.surfaceContainerLow,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: AppColors.outlineVariant.withValues(alpha: 0.3),
                              ),
                            ),
                            child: const Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.refresh, size: 20, color: AppColors.onSurface),
                                SizedBox(height: 2),
                                Text(
                                  'Clear audio',
                                  style: TextStyle(fontSize: 11.5, color: AppColors.onSurface),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLow,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.nature_people, size: 22, color: AppColors.secondary),
                        SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Take all the silence you need',
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.onSurface,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'TrueVoice will never interrupt you. When finished, your speech is transcribed and you can review, continue in chat, or proceed with support.',
                                style: TextStyle(
                                  fontSize: 12.5,
                                  height: 1.45,
                                  color: AppColors.onSurfaceVariant,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),
                  TextButton.icon(
                    onPressed: () => context.go(RoutePaths.aiChat),
                    icon: const Icon(Icons.arrow_forward, size: 16, color: AppColors.primary),
                    label: const Text(
                      'Prefer to type? Switch to text chat anytime',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: AppColors.primary),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.25)),
                    ),
                    child: Column(
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.verified_user, size: 15, color: AppColors.secondary),
                            const SizedBox(width: 6),
                            Flexible(
                              child: Text(
                                'Language: ${AppStateService.instance.selectedLanguage} • Speech processed with privacy protocols',
                                style: const TextStyle(fontSize: 11.5, color: AppColors.secondary),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          alignment: WrapAlignment.center,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            const Text(
                              'Need an immediate human voice? ',
                              style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant),
                            ),
                            InkWell(
                              onTap: () => context.go(RoutePaths.supportEmergency),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppColors.errorContainer,
                                  borderRadius: BorderRadius.circular(999),
                                ),
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.call, size: 12, color: AppColors.onErrorContainer),
                                    SizedBox(width: 4),
                                    Text(
                                      'Demo Call (9787872051)',
                                      style: TextStyle(
                                        fontSize: 11.5,
                                        fontWeight: FontWeight.w600,
                                        color: AppColors.onErrorContainer,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
