import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';

enum GroundingState {
  intro,
  inhale,
  hold,
  exhale,
  complete,
}

/// Full-screen guided breathing & grounding sanctuary experience.
///
/// Designed with TrueVoice trauma-informed visual principles:
/// - Warm ivory background (#F8FAF6)
/// - Sage green (#335941) & soft olive (#596244)
/// - Deep charcoal typography (#191C1A)
/// - 4-4-4 rhythm: 4s Inhale, 4s Hold, 4s Exhale
/// - 3 gentle guided cycles with explicit user control
class GroundingPage extends StatefulWidget {
  const GroundingPage({super.key});

  @override
  State<GroundingPage> createState() => _GroundingPageState();
}

class _GroundingPageState extends State<GroundingPage> with SingleTickerProviderStateMixin {
  GroundingState _state = GroundingState.intro;
  int _currentCycle = 1;
  static const int _totalCycles = 3;
  int _secondsRemaining = 4;

  Timer? _countdownTimer;
  late final AnimationController _circleAnimController;
  late final Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _circleAnimController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    );

    _scaleAnimation = Tween<double>(begin: 0.72, end: 1.0).animate(
      CurvedAnimation(
        parent: _circleAnimController,
        curve: Curves.easeInOutCubic,
      ),
    );
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _circleAnimController.dispose();
    super.dispose();
  }

  void _handleExit() {
    _countdownTimer?.cancel();
    _circleAnimController.stop();
    if (mounted) {
      if (Navigator.of(context).canPop()) {
        context.pop();
      } else {
        context.go(RoutePaths.aiChat);
      }
    }
  }

  void _startExercise() {
    setState(() {
      _currentCycle = 1;
      _secondsRemaining = 4;
      _state = GroundingState.inhale;
    });
    _runInhale();
  }

  void _runInhale() {
    if (!mounted) return;
    setState(() {
      _state = GroundingState.inhale;
      _secondsRemaining = 4;
    });
    _circleAnimController.duration = const Duration(seconds: 4);
    _circleAnimController.forward(from: 0.0);
    _startCountdown(() {
      _runHold();
    });
  }

  void _runHold() {
    if (!mounted) return;
    setState(() {
      _state = GroundingState.hold;
      _secondsRemaining = 4;
    });
    // Keep circle expanded during hold
    _circleAnimController.value = 1.0;
    _startCountdown(() {
      _runExhale();
    });
  }

  void _runExhale() {
    if (!mounted) return;
    setState(() {
      _state = GroundingState.exhale;
      _secondsRemaining = 4;
    });
    _circleAnimController.duration = const Duration(seconds: 4);
    _circleAnimController.reverse(from: 1.0);
    _startCountdown(() {
      if (_currentCycle < _totalCycles) {
        setState(() {
          _currentCycle++;
        });
        _runInhale();
      } else {
        _finishExercise();
      }
    });
  }

  void _startCountdown(VoidCallback onComplete) {
    _countdownTimer?.cancel();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_secondsRemaining > 1) {
        setState(() {
          _secondsRemaining--;
        });
      } else {
        timer.cancel();
        onComplete();
      }
    });
  }

  void _finishExercise() {
    _countdownTimer?.cancel();
    if (mounted) {
      setState(() {
        _state = GroundingState.complete;
      });
    }
  }

  String _getPhaseTitle() {
    switch (_state) {
      case GroundingState.intro:
        return 'Take a breath.';
      case GroundingState.inhale:
        return 'INHALE';
      case GroundingState.hold:
        return 'HOLD';
      case GroundingState.exhale:
        return 'EXHALE';
      case GroundingState.complete:
        return "You're here.";
    }
  }

  String _getPhaseSubtitle() {
    switch (_state) {
      case GroundingState.intro:
        return "Let's take a few slow breaths together.";
      case GroundingState.inhale:
        return 'Breathe in slowly';
      case GroundingState.hold:
        return 'Keep still for a moment';
      case GroundingState.exhale:
        return 'Let your breath out slowly';
      case GroundingState.complete:
        return 'Take one more comfortable breath.';
    }
  }

  String _getSemanticAnnouncement() {
    switch (_state) {
      case GroundingState.intro:
        return 'Take a breath. Let us take a few slow breaths together.';
      case GroundingState.inhale:
        return 'Inhale. Breathe in slowly. $_secondsRemaining seconds remaining.';
      case GroundingState.hold:
        return 'Hold. Keep still for a moment. $_secondsRemaining seconds remaining.';
      case GroundingState.exhale:
        return 'Exhale. Let your breath out slowly. $_secondsRemaining seconds remaining.';
      case GroundingState.complete:
        return 'You are here. Take one more comfortable breath.';
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) {
          _handleExit();
        }
      },
      child: Scaffold(
        backgroundColor: AppColors.surface,
        appBar: AppBar(
          backgroundColor: AppColors.surface,
          elevation: 0,
          leading: IconButton(
            icon: const Icon(Icons.arrow_back, color: AppColors.onSurface),
            tooltip: 'Back to chat',
            onPressed: _handleExit,
          ),
          centerTitle: true,
          title: const Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Grounding Moment',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: AppColors.onSurface,
                ),
              ),
              SizedBox(height: 1),
              Text(
                'Take a moment for yourself',
                style: TextStyle(
                  fontSize: 11.5,
                  color: AppColors.secondaryOlive,
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: _handleExit,
              child: const Text(
                'Skip',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.secondaryOlive,
                ),
              ),
            ),
            const SizedBox(width: 8),
          ],
        ),
        body: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Semantics(
                label: _getSemanticAnnouncement(),
                liveRegion: true,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  child: Column(
                    children: [
                      const Spacer(flex: 1),

                      // Main Title & Guidance Subtitle
                      Text(
                        _getPhaseTitle(),
                        style: TextStyle(
                          fontSize: _state == GroundingState.intro || _state == GroundingState.complete ? 28 : 22,
                          fontWeight: FontWeight.w700,
                          letterSpacing: _state == GroundingState.intro || _state == GroundingState.complete ? -0.5 : 2.0,
                          color: AppColors.onSurface,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _getPhaseSubtitle(),
                        style: const TextStyle(
                          fontSize: 14.5,
                          height: 1.4,
                          color: AppColors.onSurfaceVariant,
                        ),
                        textAlign: TextAlign.center,
                      ),

                      const Spacer(flex: 2),

                      // Large Central Therapeutic Breathing Visual
                      _buildBreathingVisual(),

                      const Spacer(flex: 2),

                      // Phase State Indicators & Actions
                      if (_state == GroundingState.intro)
                        _buildIntroAction()
                      else if (_state == GroundingState.complete)
                        _buildCompleteAction()
                      else
                        _buildActiveCycleControls(),

                      const Spacer(flex: 1),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBreathingVisual() {
    return AnimatedBuilder(
      animation: _circleAnimController,
      builder: (context, child) {
        final scale = _scaleAnimation.value;
        return SizedBox(
          width: 240,
          height: 240,
          child: Stack(
            alignment: Alignment.center,
            children: [
              // Outer soothing soft olive halo
              Transform.scale(
                scale: scale,
                child: Container(
                  width: 230,
                  height: 230,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.secondaryContainer.withValues(alpha: 0.35),
                  ),
                ),
              ),
              // Middle gentle organic layer
              Transform.scale(
                scale: 0.88 * scale,
                child: Container(
                  width: 200,
                  height: 200,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.secondaryContainer.withValues(alpha: 0.65),
                  ),
                ),
              ),
              // Inner therapeutic sage green core
              Transform.scale(
                scale: 0.74 * scale,
                child: Container(
                  width: 170,
                  height: 170,
                  decoration: const BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppColors.primarySage,
                  ),
                  child: Center(
                    child: _state == GroundingState.intro
                        ? const Icon(
                            Icons.spa_outlined,
                            size: 46,
                            color: Colors.white,
                          )
                        : _state == GroundingState.complete
                            ? const Icon(
                                Icons.check,
                                size: 50,
                                color: Colors.white,
                              )
                            : AnimatedSwitcher(
                                duration: const Duration(milliseconds: 250),
                                transitionBuilder: (child, anim) => FadeTransition(
                                  opacity: anim,
                                  child: ScaleTransition(scale: anim, child: child),
                                ),
                                child: Text(
                                  '$_secondsRemaining',
                                  key: ValueKey<int>(_secondsRemaining),
                                  style: const TextStyle(
                                    fontSize: 48,
                                    fontWeight: FontWeight.w700,
                                    color: Colors.white,
                                    letterSpacing: -1,
                                  ),
                                ),
                              ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildIntroAction() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: double.infinity,
          height: 52,
          child: FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            onPressed: _startExercise,
            child: const Text(
              'Begin',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        ),
        const SizedBox(height: 14),
        const Text(
          '3 slow cycles (36 seconds) • You can stop anytime',
          style: TextStyle(fontSize: 12, color: AppColors.secondaryOlive),
        ),
      ],
    );
  }

  Widget _buildActiveCycleControls() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        // Subtle minimal cycle indicator dots (● ○ ○)
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            for (int i = 1; i <= _totalCycles; i++) ...[
              Container(
                width: 8,
                height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: i == _currentCycle
                      ? AppColors.primary
                      : i < _currentCycle
                          ? AppColors.primarySage.withValues(alpha: 0.5)
                          : AppColors.outlineVariant.withValues(alpha: 0.5),
                ),
              ),
              if (i < _totalCycles) const SizedBox(width: 8),
            ],
          ],
        ),
        const SizedBox(height: 10),
        Text(
          'Cycle $_currentCycle of $_totalCycles',
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: AppColors.secondaryOlive,
          ),
        ),
        const SizedBox(height: 20),
        const Text(
          'You can stop anytime',
          style: TextStyle(
            fontSize: 12,
            color: AppColors.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _buildCompleteAction() {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.secondaryContainer.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(999),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.check_circle, size: 14, color: AppColors.primary),
              SizedBox(width: 6),
              Text(
                'Grounding complete',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppColors.primary,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        SizedBox(
          width: double.infinity,
          height: 52,
          child: FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 0,
            ),
            onPressed: _handleExit,
            child: const Text(
              'Continue',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
            ),
          ),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: _handleExit,
          child: const Text(
            "I'm done",
            style: TextStyle(
              fontSize: 14,
              color: AppColors.secondaryOlive,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }
}
