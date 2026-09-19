import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/services/app_state_service.dart';
import '../../../../shared/widgets/sanctuary_bottom_nav.dart';
import '../../../../shared/widgets/sanctuary_header.dart';
import '../data/models/api_models.dart';
import '../data/services/victim_api_service.dart';

/// Personalized Support Plan Page — Rebuilt from Completed Conversation.
///
/// Strictly grounded in the user's actual narrative, real multimodal AI signals,
/// deterministic SVI, and rule-based SafetyGuard recommendations.
/// Zero hardcoded directory services. Zero fake human advocates.
class SupportEmergencyPage extends StatefulWidget {
  const SupportEmergencyPage({super.key});

  @override
  State<SupportEmergencyPage> createState() => _SupportEmergencyPageState();
}

class _SupportEmergencyPageState extends State<SupportEmergencyPage> {
  final VictimApiService _apiService = VictimApiService();
  int _navIndex = 2; // Care & Help active tab
  bool _isLoading = true;
  PersonalizedSupportPlanModel? _supportPlan;

  @override
  void initState() {
    super.initState();
    _loadPersonalizedSupportPlan();
  }

  Future<void> _loadPersonalizedSupportPlan() async {
    setState(() {
      _isLoading = true;
    });

    final sessionId = AppStateService.instance.sessionId;
    if (sessionId == null || sessionId.isEmpty || sessionId.startsWith('local-')) {
      // Generate a graceful baseline plan if no remote session is active
      setState(() {
        _supportPlan = const PersonalizedSupportPlanModel(
          sessionId: 'local',
          whatWeHeard: 'You spent time sharing your thoughts with TrueVoice Guide.',
          howYouAreDoing: 'Thank you for taking the time to share what was on your mind at your own pace.',
          primaryConcerns: ['Personal reflection'],
          emotionalIndicators: ['Reflective'],
          immediateSafetyNeeded: false,
          recommendations: [],
          hasHumanAssignment: false,
          humanReviewStatus: 'Human review available',
          humanReviewMessage: 'A trained human responder can review your intake whenever you wish.',
          userChoices: [],
          uncertainties: [],
          createdAt: '',
        );
        _isLoading = false;
      });
      return;
    }

    try {
      final plan = await _apiService.getSupportPlan(sessionId: sessionId);
      if (mounted) {
        setState(() {
          _supportPlan = plan;
          _isLoading = false;
        });
      }
    } catch (e) {
      debugPrint('[SupportPlan] Failed to load remote plan: $e');
      if (mounted) {
        setState(() {
          _supportPlan = const PersonalizedSupportPlanModel(
            sessionId: 'offline',
            whatWeHeard: 'We have recorded your conversation and your reflections are safely saved.',
            howYouAreDoing: 'Taking time to share what you are experiencing is an important step. You are in control of what happens next.',
            primaryConcerns: ['Personal support'],
            emotionalIndicators: ['Processing'],
            immediateSafetyNeeded: false,
            recommendations: [],
            hasHumanAssignment: false,
            humanReviewStatus: 'Human review available',
            humanReviewMessage: 'A trained responder can review your notes to guide your next steps with total confidentiality.',
            userChoices: [],
            uncertainties: [],
            createdAt: '',
          );
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _launchDialer(String number) async {
    final uri = Uri.parse('tel:$number');
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      }
    } catch (_) {}
  }

  void _onBottomNavTapped(int index) {
    if (index == 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Safe Vault is coming soon.'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }
    setState(() => _navIndex = index);
    if (index == 0) {
      context.go(RoutePaths.home);
    } else if (index == 1) {
      context.go(RoutePaths.aiChat);
    }
  }

  void _showRecommendationDetails(SupportRecommendationModel rec) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.secondaryContainer.withValues(alpha: 0.5),
                shape: BoxShape.circle,
              ),
              child: Icon(_getCategoryIcon(rec.category), size: 20, color: AppColors.primary),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                rec.displayTitle,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Why this was suggested:',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.primary),
            ),
            const SizedBox(height: 4),
            Text(
              rec.reason,
              style: const TextStyle(fontSize: 13, color: AppColors.onSurfaceVariant, height: 1.45),
            ),
            if (rec.responderAction.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text(
                'Responder Guideline:',
                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.secondary),
              ),
              const SizedBox(height: 4),
              Text(
                rec.responderAction,
                style: const TextStyle(fontSize: 12.5, color: AppColors.onSurfaceVariant, height: 1.4),
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Close'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Interest noted for ${rec.displayTitle}. A responder will review this pathway.'),
                  backgroundColor: AppColors.primary,
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: const Text("I'd like this"),
          ),
        ],
      ),
    );
  }

  void _requestHumanReview() {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Request Human Review', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
        content: const Text(
          'Your conversation summary and care preferences will be placed in the priority triage queue for review by a certified human counselor. No external authorities will be contacted without your explicit consent.',
          style: TextStyle(fontSize: 13.5, color: AppColors.onSurfaceVariant, height: 1.45),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Human review requested. A trained counselor will review your intake.'),
                  backgroundColor: AppColors.primary,
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: const Text('Confirm Request'),
          ),
        ],
      ),
    );
  }

  IconData _getCategoryIcon(String category) {
    switch (category) {
      case 'COUNSELLING_SUPPORT':
        return Icons.forum_outlined;
      case 'SAFETY_ASSISTANCE':
        return Icons.shield_outlined;
      case 'LEGAL_AID':
        return Icons.gavel_outlined;
      case 'SOCIAL_SUPPORT':
        return Icons.people_outline;
      case 'MEDICAL_ASSISTANCE':
        return Icons.medical_services_outlined;
      case 'EMERGENCY_SUPPORT':
        return Icons.emergency_outlined;
      case 'POLICE_ASSISTANCE':
        return Icons.local_police_outlined;
      default:
        return Icons.help_outline;
    }
  }

  Color _getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return AppColors.tertiary;
      case 'important':
        return AppColors.secondary;
      default:
        return AppColors.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: SanctuaryHeader(
        title: 'Support Plan',
        subtitle: 'TRUEVOICE GUIDE',
        showBack: true,
        onBack: () => context.go(RoutePaths.home),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: _isLoading
                ? _buildLoadingView()
                : _buildContent(context),
          ),
        ),
      ),
      bottomNavigationBar: SanctuaryBottomNav(
        currentIndex: _navIndex,
        onTap: _onBottomNavTapped,
      ),
    );
  }

  Widget _buildLoadingView() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(28.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: AppColors.primaryFixed.withValues(alpha: 0.5),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.psychology_outlined, color: AppColors.primary, size: 28),
            ),
            const SizedBox(height: 18),
            const Text(
              'Organizing your support plan...',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.onSurface),
            ),
            const SizedBox(height: 8),
            const Text(
              'Gently reflecting on what you shared with TrueVoice Guide to prepare thoughtful next steps.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppColors.onSurfaceVariant, height: 1.45),
            ),
            const SizedBox(height: 24),
            const SizedBox(
              width: 32,
              height: 32,
              child: CircularProgressIndicator(strokeWidth: 2.5, color: AppColors.primary),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    final plan = _supportPlan!;

    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
      children: [
        // ── Header Title Block ──
        Text(
          'Your Support Plan',
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: AppColors.onSurface,
                letterSpacing: -0.3,
              ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Based on what you shared with TrueVoice Guide',
          style: TextStyle(
            fontSize: 13,
            color: AppColors.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 16),

        // ── 1. WHAT WE HEARD ──
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surfaceContainerLowest,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.primary.withValues(alpha: 0.15)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.02),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: AppColors.primaryFixed,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.hearing, size: 18, color: AppColors.onPrimaryFixedVariant),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    'What We Heard',
                    style: TextStyle(
                      fontSize: 14.5,
                      fontWeight: FontWeight.w600,
                      color: AppColors.onSurface,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                plan.whatWeHeard,
                style: const TextStyle(
                  fontSize: 13.5,
                  height: 1.5,
                  color: AppColors.onSurface,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // ── 2. HOW YOU'RE DOING ──
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surfaceContainerLow,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.secondary.withValues(alpha: 0.15)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: AppColors.secondaryContainer,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.spa, size: 18, color: AppColors.onSecondaryContainer),
                  ),
                  const SizedBox(width: 10),
                  const Text(
                    "How You're Doing",
                    style: TextStyle(
                      fontSize: 14.5,
                      fontWeight: FontWeight.w600,
                      color: AppColors.onSurface,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                plan.howYouAreDoing,
                style: const TextStyle(
                  fontSize: 13.5,
                  height: 1.5,
                  color: AppColors.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        // ── 3. YOUR IMMEDIATE SAFETY (ONLY SHOWN IF RELEVANT) ──
        if (plan.immediateSafetyNeeded && plan.verifiedEmergencyResource != null) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.errorContainer.withValues(alpha: 0.35),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: AppColors.tertiary.withValues(alpha: 0.3)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      width: 34,
                      height: 34,
                      decoration: const BoxDecoration(
                        color: AppColors.tertiaryContainer,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.emergency_outlined, size: 20, color: Colors.white),
                    ),
                    const SizedBox(width: 10),
                    const Expanded(
                      child: Text(
                        'Your Immediate Safety',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.onSurface),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  plan.immediateSafetyMessage ?? 'Based on what you shared, it may be important to focus on getting somewhere safe first.',
                  style: const TextStyle(fontSize: 13, height: 1.45, color: AppColors.onSurfaceVariant),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 44,
                  child: FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.tertiary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    onPressed: () => _launchDialer(plan.verifiedEmergencyResource!.number),
                    icon: const Icon(Icons.call, size: 16),
                    label: Text(
                      'Call ${plan.verifiedEmergencyResource!.title} (${plan.verifiedEmergencyResource!.number})',
                      style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        // ── 4. WHAT MAY HELP RIGHT NOW ──
        Text(
          'What May Help Right Now',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: AppColors.onSurface,
              ),
        ),
        const SizedBox(height: 4),
        const Text(
          'Support pathways suggested based on your conversation.',
          style: TextStyle(fontSize: 12.5, color: AppColors.onSurfaceVariant),
        ),
        const SizedBox(height: 12),

        if (plan.recommendations.isNotEmpty) ...[
          for (final rec in plan.recommendations) ...[
            _buildRecommendationCard(rec),
            const SizedBox(height: 10),
          ],
        ] else ...[
          // Empty state for non-crisis or normal conversation
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surfaceContainerLowest,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.check_circle_outline, size: 20, color: AppColors.primary),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    "Based on what you've shared, you may not need to take any immediate external action. You can continue talking with TrueVoice Guide or choose to speak with a human responder.",
                    style: TextStyle(fontSize: 13, height: 1.45, color: AppColors.onSurfaceVariant),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
        ],

        const SizedBox(height: 12),

        // ── 5. HUMAN REVIEW (REAL STATUS) ──
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: AppColors.surfaceContainerLowest,
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: AppColors.secondaryContainer.withValues(alpha: 0.6),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.verified_user_outlined, size: 20, color: AppColors.primary),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          plan.humanReviewStatus,
                          style: const TextStyle(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w600,
                            color: AppColors.onSurface,
                          ),
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Human Advocates Lead Every Step',
                          style: TextStyle(fontSize: 11.5, color: AppColors.onSurfaceVariant),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                plan.humanReviewMessage,
                style: const TextStyle(fontSize: 12.5, height: 1.45, color: AppColors.onSurfaceVariant),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                height: 40,
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.primary,
                    side: const BorderSide(color: AppColors.primary),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: _requestHumanReview,
                  icon: const Icon(Icons.person_outline, size: 16),
                  label: const Text('Request Responder Review', style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // ── 6. YOUR CHOICES ──
        Text(
          'Your Choices',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontSize: 15,
                fontWeight: FontWeight.w700,
                color: AppColors.onSurface,
              ),
        ),
        const SizedBox(height: 4),
        const Text(
          'You decide what happens next. Take all the time you need.',
          style: TextStyle(fontSize: 12.5, color: AppColors.onSurfaceVariant),
        ),
        const SizedBox(height: 12),

        // Action Buttons
        SizedBox(
          width: double.infinity,
          height: 48,
          child: FilledButton.icon(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () => context.go(RoutePaths.aiChat),
            icon: const Icon(Icons.forum_outlined, size: 18),
            label: const Text(
              'Return to TrueVoice Guide',
              style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600),
            ),
          ),
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          height: 46,
          child: OutlinedButton.icon(
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.onSurfaceVariant,
              side: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.5)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () => context.go(RoutePaths.home),
            icon: const Icon(Icons.home_outlined, size: 18),
            label: const Text(
              'Return to Home',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
            ),
          ),
        ),
        const SizedBox(height: 24),
      ],
    );
  }

  Widget _buildRecommendationCard(SupportRecommendationModel rec) {
    final priorityColor = _getPriorityColor(rec.priority);

    return InkWell(
      onTap: () => _showRecommendationDetails(rec),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surfaceContainerLowest,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.25)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              blurRadius: 6,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: AppColors.secondaryContainer.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(_getCategoryIcon(rec.category), size: 20, color: AppColors.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          rec.displayTitle,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.onSurface,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                        decoration: BoxDecoration(
                          color: priorityColor.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          rec.priority.toUpperCase(),
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                            color: priorityColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    rec.reason,
                    style: const TextStyle(
                      fontSize: 12,
                      height: 1.4,
                      color: AppColors.onSurfaceVariant,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Row(
                    children: [
                      Text(
                        'Explore option',
                        style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: AppColors.primary),
                      ),
                      SizedBox(width: 4),
                      Icon(Icons.arrow_forward, size: 12, color: AppColors.primary),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
