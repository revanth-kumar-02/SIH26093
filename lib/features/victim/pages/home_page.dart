import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/constants/app_strings.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/app_state_service.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/crisis_banner.dart';
import '../../../../shared/widgets/sanctuary_bottom_nav.dart';
import '../../../../shared/widgets/sanctuary_header.dart';

/// Screen 5: Home / Help — Source of Truth from Stitch.
///
/// Serves as the central emotional shelter, offering the victim
/// two distinct trauma-informed intake choices (Voice vs Text),
/// draft resumption, quick language switching, and immediate crisis helpline access.
class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int _navIndex = 0;

  @override
  void initState() {
    super.initState();
    AppStateService.instance.addListener(_onAppStateChanged);
  }

  void _onAppStateChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    AppStateService.instance.removeListener(_onAppStateChanged);
    super.dispose();
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
    if (index == 1) {
      context.go(RoutePaths.aiChat);
    } else if (index == 2) {
      context.go(RoutePaths.supportEmergency);
    }
  }

  void _toggleLanguage() {
    final langs = ['English', 'Hindi', 'Tamil', 'Telugu', 'Kannada', 'Malayalam'];
    final current = AppStateService.instance.selectedLanguage;
    final nextIdx = (langs.indexOf(current) + 1) % langs.length;
    AppStateService.instance.setLanguage(langs[nextIdx]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: SanctuaryHeader(
        title: AppStrings.tr('sanctuary_home'),
        subtitle: AppStrings.tr('nhaa_sanctuary'),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
              children: [
                // Privacy & State Reassurance Chip + Language Pill
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Flexible(
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceContainerLow,
                          borderRadius: BorderRadius.circular(999),
                        border: Border.all(
                          color: AppColors.outlineVariant.withValues(alpha: 0.3),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.shield, size: 14, color: AppColors.primarySage),
                          const SizedBox(width: 6),
                          Flexible(
                            child: Text(
                              AppStrings.tr('safe_encrypted'),
                              style: const TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w500,
                                color: AppColors.secondaryOlive,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                    InkWell(
                      onTap: _toggleLanguage,
                      borderRadius: BorderRadius.circular(999),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceContainerLowest,
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: AppColors.outlineVariant.withValues(alpha: 0.3),
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.translate, size: 14, color: AppColors.secondaryOlive),
                            const SizedBox(width: 4),
                            Text(
                              AppStateService.instance.selectedLanguage,
                              style: const TextStyle(
                                fontSize: 11.5,
                                fontWeight: FontWeight.w500,
                                color: AppColors.onSurfaceVariant,
                              ),
                            ),
                            const SizedBox(width: 2),
                            const Icon(Icons.expand_more, size: 14, color: AppColors.outline),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),

                // Organic Presence & Emotional Shelter Hero
                Container(
                  width: double.infinity,
                  height: 140,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(18),
                    color: AppColors.surfaceContainerLow,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.03),
                        blurRadius: 10,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(18),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        Image.asset(
                          'assets/images/home_eucalyptus.png',
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) => Container(
                            color: AppColors.secondaryContainer.withValues(alpha: 0.4),
                            child: const Icon(Icons.spa, size: 48, color: AppColors.primarySage),
                          ),
                        ),
                        // Gentle gradient overlay
                        Container(
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.bottomCenter,
                              end: Alignment.topCenter,
                              colors: [
                                AppColors.surface.withValues(alpha: 0.85),
                                AppColors.surface.withValues(alpha: 0.3),
                                Colors.transparent,
                              ],
                            ),
                          ),
                        ),
                        // Active status pill
                        Positioned(
                          bottom: 12,
                          left: 14,
                          child: Row(
                            children: [
                              Container(
                                width: 8,
                                height: 8,
                                decoration: const BoxDecoration(
                                  color: AppColors.primarySage,
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              const Text(
                                'SAFE TRUEVOICE ACTIVE',
                                style: TextStyle(
                                  fontSize: 10.5,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 0.8,
                                  color: AppColors.secondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 18),

                // Warm Conversational Greeting
                Text(
                  AppStrings.tr('how_share'),
                  style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                        fontSize: 21,
                        height: 28 / 21,
                        fontWeight: FontWeight.w600,
                        color: AppColors.onSurface,
                        letterSpacing: -0.2,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  AppStrings.tr('choose_pace'),
                  style: const TextStyle(
                    fontSize: 14,
                    height: 1.5,
                    color: AppColors.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 16),

                // Resume Draft Banner (Dynamic - only displayed when an actual intake draft exists)
                Builder(
                  builder: (context) {
                    final draft = AppStateService.instance.activeDraft;
                    if (draft == null) {
                      return const SizedBox.shrink();
                    }
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 16),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        decoration: BoxDecoration(
                          color: AppColors.secondaryContainer.withValues(alpha: 0.5),
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: AppColors.secondaryContainer,
                            width: 1,
                          ),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 34,
                              height: 34,
                              decoration: const BoxDecoration(
                                color: AppColors.surfaceContainerLowest,
                                shape: BoxShape.circle,
                              ),
                              child: Icon(
                                draft.type == 'voice' ? Icons.mic : Icons.history_edu,
                                size: 18,
                                color: AppColors.secondary,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Resume where you paused',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: AppColors.onSecondaryFixed,
                                    ),
                                  ),
                                  const SizedBox(height: 1),
                                  Text(
                                    '${draft.previewText} • ${draft.timeAgo}',
                                    style: const TextStyle(
                                      fontSize: 11.5,
                                      color: AppColors.onSecondaryContainer,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            TextButton(
                              style: TextButton.styleFrom(
                                backgroundColor: AppColors.surfaceContainerLowest,
                                foregroundColor: AppColors.primary,
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                minimumSize: Size.zero,
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                              ),
                              onPressed: () => context.go(
                                draft.type == 'voice' ? RoutePaths.voiceInteraction : RoutePaths.aiChat,
                              ),
                              child: const Text(
                                'Resume',
                                style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                              ),
                            ),
                            const SizedBox(width: 4),
                            IconButton(
                              icon: const Icon(Icons.close, size: 16, color: AppColors.onSecondaryContainer),
                              padding: EdgeInsets.zero,
                              constraints: const BoxConstraints(minWidth: 24, minHeight: 24),
                              tooltip: 'Dismiss draft',
                              onPressed: () => AppStateService.instance.clearDraft(),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 18),

                // Option 1: Voice Choice Card
                _buildChoiceCard(
                  icon: Icons.mic,
                  title: AppStrings.tr('talk_with_us'),
                  subtitle: 'Gentle voice listening',
                  description: AppStrings.tr('talk_subtitle'),
                  actionLabel: 'Start voice conversation',
                  badgeLabel: 'Audio',
                  secondaryIcon: Icons.volume_up,
                  onTap: () => context.go(RoutePaths.voiceInteraction),
                ),
                const SizedBox(height: 14),

                // Option 2: Written Choice Card
                _buildChoiceCard(
                  icon: Icons.edit_note,
                  title: AppStrings.tr('type_it_out'),
                  subtitle: 'Guided written pacing',
                  description: AppStrings.tr('type_subtitle'),
                  actionLabel: 'Start written conversation',
                  badgeLabel: 'Text',
                  secondaryIcon: Icons.pause_circle_outline,
                  onTap: () => context.go(RoutePaths.aiChat),
                ),
                const SizedBox(height: 18),

                // Reassurance & Autonomy Card
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: EdgeInsets.only(top: 2),
                        child: Icon(
                          Icons.lock_reset,
                          size: 18,
                          color: AppColors.secondary,
                        ),
                      ),
                      SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Your comfort and autonomy come first',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w600,
                                color: AppColors.onSurface,
                              ),
                            ),
                            SizedBox(height: 3),
                            Text(
                              'Everything shared is encrypted & confidential. You can pause, save as draft, or step away at any moment without losing your thoughts.',
                              style: TextStyle(
                                fontSize: 12,
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

                // Urgent Crisis Safety Bar
                const CrisisBanner(),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: SanctuaryBottomNav(
        currentIndex: _navIndex,
        onTap: _onBottomNavTapped,
      ),
    );
  }

  Widget _buildChoiceCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required String description,
    required String actionLabel,
    required String badgeLabel,
    required IconData secondaryIcon,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: AppColors.surfaceContainerLowest,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: AppColors.outlineVariant.withValues(alpha: 0.3),
          ),
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
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: const BoxDecoration(
                    color: AppColors.secondaryContainer,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, size: 24, color: AppColors.primary),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: AppColors.onSurface,
                        ),
                      ),
                      const SizedBox(height: 1),
                      Text(
                        subtitle,
                        style: const TextStyle(
                          fontSize: 11.5,
                          color: AppColors.secondary,
                        ),
                      ),
                    ],
                  ),
                ),
                Icon(secondaryIcon, size: 20, color: AppColors.outline),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              description,
              style: const TextStyle(
                fontSize: 13.5,
                height: 1.45,
                color: AppColors.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 14),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Flexible(
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Flexible(
                        child: Text(
                          actionLabel,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.primary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 4),
                      const Icon(Icons.arrow_forward, size: 16, color: AppColors.primary),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(999),
                  ),
                  child: Text(
                    badgeLabel,
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w500,
                      color: AppColors.secondary,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
