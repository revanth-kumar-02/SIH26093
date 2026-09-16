import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/crisis_banner.dart';
import '../../../../shared/widgets/sanctuary_header.dart';

/// Screen 8: Assessment Status - Source of Truth from Stitch.
///
/// Clearly shows the supportive triage intake status, affirming that human counselors
/// lead all decisions, and smoothly transitions to care & support options.
class AssessmentStatusPage extends StatefulWidget {
  const AssessmentStatusPage({super.key});

  @override
  State<AssessmentStatusPage> createState() => _AssessmentStatusPageState();
}

class _AssessmentStatusPageState extends State<AssessmentStatusPage> {
  /// 0 = none complete, 1 = step 1 done, 2 = step 2 done, 3 = all done
  int _currentStep = 0;
  Timer? _timer1;
  Timer? _timer2;
  Timer? _timer3;

  @override
  void initState() {
    super.initState();
    _startProgressSequence();
  }

  void _startProgressSequence() {
    _timer1 = Timer(const Duration(milliseconds: 1500), () {
      if (mounted) setState(() => _currentStep = 1);
    });
    _timer2 = Timer(const Duration(milliseconds: 3500), () {
      if (mounted) setState(() => _currentStep = 2);
    });
    _timer3 = Timer(const Duration(milliseconds: 5000), () {
      if (mounted) setState(() => _currentStep = 3);
    });
  }

  @override
  void dispose() {
    _timer1?.cancel();
    _timer2?.cancel();
    _timer3?.cancel();
    super.dispose();
  }

  double get _progressValue {
    switch (_currentStep) {
      case 0: return 0.05;
      case 1: return 0.35;
      case 2: return 0.70;
      case 3: return 1.0;
      default: return 0.0;
    }
  }

  String get _progressPercent {
    return '${(_progressValue * 100).round()}%';
  }

  String get _progressLabel {
    if (_currentStep < 3) return 'Processing your intake...';
    return 'Human care pathway prepared';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: SanctuaryHeader(
        title: 'Intake Status',
        subtitle: 'NHAA SANCTUARY',
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
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Page Heading
                  Text(
                    'Supportive intake status',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontSize: 22,
                          fontWeight: FontWeight.w600,
                          color: AppColors.onSurface,
                          letterSpacing: -0.3,
                        ),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Our trauma-informed system is organizing your shared experience to help human advocates provide the right care.',
                    style: TextStyle(
                      fontSize: 13.5,
                      height: 1.5,
                      color: AppColors.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Steps Card
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.25)),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.03),
                          blurRadius: 10,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Column(
                      children: [
                        // Step 1
                        _buildStepRow(
                          icon: _currentStep >= 1 ? Icons.check : Icons.hourglass_top,
                          iconBg: _currentStep >= 1 ? AppColors.primary : AppColors.surfaceContainerHigh,
                          iconColor: _currentStep >= 1 ? Colors.white : AppColors.onSurfaceVariant,
                          title: 'Reviewing your shared experience',
                          statusText: _currentStep >= 1 ? 'Completed' : 'Processing...',
                          statusColor: _currentStep >= 1 ? AppColors.primary : AppColors.secondary,
                          description: 'Gently parsing key details, dates, and emotional context you provided.',
                          showDivider: true,
                        ),
                        // Step 2
                        _buildStepRow(
                          icon: _currentStep >= 2 ? Icons.check : (_currentStep >= 1 ? Icons.hourglass_top : Icons.circle_outlined),
                          iconBg: _currentStep >= 2 ? AppColors.primary : (_currentStep >= 1 ? AppColors.surfaceContainerHigh : AppColors.surfaceContainer),
                          iconColor: _currentStep >= 2 ? Colors.white : AppColors.onSurfaceVariant,
                          title: 'Identifying key care & safety needs',
                          statusText: _currentStep >= 2 ? 'Completed' : (_currentStep >= 1 ? 'Processing...' : 'Pending'),
                          statusColor: _currentStep >= 2 ? AppColors.primary : AppColors.secondary,
                          description: 'Highlighting areas where immediate safety, emotional care, or legal guidance may be helpful.',
                          showDivider: true,
                        ),
                        // Step 3
                        _buildStepRow(
                          icon: _currentStep >= 3 ? Icons.support_agent : (_currentStep >= 2 ? Icons.hourglass_top : Icons.circle_outlined),
                          iconBg: _currentStep >= 3 ? AppColors.primaryFixed : (_currentStep >= 2 ? AppColors.surfaceContainerHigh : AppColors.surfaceContainer),
                          iconColor: _currentStep >= 3 ? AppColors.onPrimaryFixedVariant : AppColors.onSurfaceVariant,
                          title: 'Connecting with human responder',
                          statusText: _currentStep >= 3 ? 'Ready to assign' : (_currentStep >= 2 ? 'Processing...' : 'Pending'),
                          statusColor: _currentStep >= 3 ? AppColors.secondary : AppColors.outline,
                          description: 'A trained counselor will review these insights before recommending supportive next steps.',
                          showDivider: false,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Human Advocates Card
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLow,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          width: 34,
                          height: 34,
                          decoration: const BoxDecoration(
                            color: AppColors.secondaryContainer,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.verified_user, size: 18, color: AppColors.onSecondaryContainer),
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Human Advocates Lead Every Step',
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.onSurface,
                                ),
                              ),
                              SizedBox(height: 4),
                              Text(
                                'This is a supportive intake assessment, not a medical or legal judgment. Every support decision remains thoughtfully guided by certified human advocates.',
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
                  const SizedBox(height: 18),

                  // Progress & Action Card
                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLowest,
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.25)),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.03),
                          blurRadius: 10,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Flexible(
                              child: Text(
                                _progressLabel,
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                  color: AppColors.secondary,
                                ),
                              ),
                            ),
                            Text(
                              _progressPercent,
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: AppColors.primary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(999),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 600),
                            curve: Curves.easeInOut,
                            child: LinearProgressIndicator(
                              value: _progressValue,
                              backgroundColor: AppColors.surfaceContainer,
                              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
                              minHeight: 8,
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: FilledButton(
                            style: FilledButton.styleFrom(
                              backgroundColor: _currentStep >= 3 ? AppColors.primary : AppColors.surfaceContainerHigh,
                              foregroundColor: _currentStep >= 3 ? Colors.white : AppColors.onSurfaceVariant,
                              elevation: _currentStep >= 3 ? 2 : 0,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(14),
                              ),
                            ),
                            onPressed: _currentStep >= 3
                                ? () => context.go(RoutePaths.supportEmergency)
                                : null,
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Flexible(
                                  child: Text(
                                    'Proceed to Support Options',
                                    style: TextStyle(fontSize: 14.5, fontWeight: FontWeight.w600),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                SizedBox(width: 8),
                                Icon(Icons.arrow_forward, size: 18),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 18),

                  // Dual Emergency Contact Bar
                  const CrisisBanner(showDualEmergency: true),
                  const SizedBox(height: 16),

                  // Privacy Footer
                  const Center(
                    child: Wrap(
                      alignment: WrapAlignment.center,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Icon(Icons.lock_outline, size: 13, color: AppColors.secondary),
                        SizedBox(width: 6),
                        Text(
                          'Private session \u2022 No data shared without consent',
                          style: TextStyle(fontSize: 11.5, color: AppColors.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStepRow({
    required IconData icon,
    required Color iconBg,
    required Color iconColor,
    required String title,
    required String statusText,
    required Color statusColor,
    required String description,
    required bool showDivider,
  }) {
    return Column(
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 400),
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: iconBg,
                shape: BoxShape.circle,
              ),
              child: Icon(icon, color: iconColor, size: 18),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          title,
                          style: const TextStyle(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w600,
                            color: AppColors.onSurface,
                          ),
                        ),
                      ),
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 300),
                        child: Container(
                          key: ValueKey(statusText),
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            statusText,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: statusColor,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 3),
                  Text(
                    description,
                    style: const TextStyle(
                      fontSize: 12.5,
                      height: 1.4,
                      color: AppColors.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        if (showDivider)
          Container(
            margin: const EdgeInsets.only(left: 17, top: 10, bottom: 10),
            height: 18,
            width: 2,
            color: AppColors.outlineVariant.withValues(alpha: 0.4),
            alignment: Alignment.centerLeft,
          ),
      ],
    );
  }
}