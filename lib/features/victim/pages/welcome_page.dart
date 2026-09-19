import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/constants/app_strings.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen 2: Welcome (Redesigned) — Source of Truth from Stitch.
///
/// Welcomes the victim with calming botanical imagery, trauma-informed
/// pacing reassurance, a direct Helpline dialer, and an intentional "Begin When Ready" CTA.
class WelcomePage extends StatelessWidget {
  const WelcomePage({super.key});

  Future<void> _launchDialer(BuildContext context, String number) async {
    final uri = Uri.parse('tel:$number');
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      } else {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Please dial $number from your phone.'),
              backgroundColor: AppColors.tertiary,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (_) {}
  }

  void _showHelplineDialog(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Row(
          children: [
            Icon(Icons.phone_in_talk, color: AppColors.tertiary, size: 22),
            SizedBox(width: 10),
            Expanded(
              child: Text(
                AppStrings.demoSupportLabel,
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Connect directly with National Emergency Helpline (112) for immediate assistance.',
              style: TextStyle(fontSize: 14, color: AppColors.onSurfaceVariant, height: 1.4),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainerLow,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
              ),
              child: const Text(
                AppStrings.demoDisclaimer,
                style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant, height: 1.4),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel', style: TextStyle(color: AppColors.onSurfaceVariant)),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.tertiary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              _launchDialer(context, AppStrings.emergencyContactNumber);
            },
            child: const Text('Call 112'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  minHeight: constraints.maxHeight,
                  maxWidth: 430,
                ),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      // 1. Discreet Top Safety Bar
                      Align(
                        alignment: Alignment.centerLeft,
                        child: InkWell(
                          onTap: () => _showHelplineDialog(context),
                          borderRadius: BorderRadius.circular(999),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            decoration: BoxDecoration(
                              color: AppColors.surfaceContainer.withValues(alpha: 0.7),
                              borderRadius: BorderRadius.circular(999),
                              border: Border.all(
                                color: AppColors.outlineVariant.withValues(alpha: 0.4),
                              ),
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.phone_in_talk, size: 15, color: AppColors.tertiary),
                                SizedBox(width: 6),
                                Text(
                                  'Emergency Helpline: ',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w500,
                                    color: AppColors.onSurfaceVariant,
                                  ),
                                ),
                                Text(
                                  '112',
                                  style: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.tertiary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 16),

                      // 2. Central Sanctuary Arch & Empathy Typography
                      Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          // Sanctuary Arch Frame
                          SizedBox(
                            width: 230,
                            height: 260,
                            child: Stack(
                              alignment: Alignment.center,
                              children: [
                                // Soft ambient back glow
                                Container(
                                  width: 240,
                                  height: 270,
                                  decoration: BoxDecoration(
                                    borderRadius: const BorderRadius.vertical(
                                      top: Radius.circular(120),
                                      bottom: Radius.circular(28),
                                    ),
                                    gradient: RadialGradient(
                                      colors: [
                                        AppColors.secondaryContainer.withValues(alpha: 0.45),
                                        AppColors.primaryFixed.withValues(alpha: 0.20),
                                        Colors.transparent,
                                      ],
                                    ),
                                  ),
                                ),
                                // Arch Image Container
                                Container(
                                  width: 220,
                                  height: 250,
                                  decoration: BoxDecoration(
                                    color: AppColors.surfaceContainerLowest,
                                    borderRadius: const BorderRadius.vertical(
                                      top: Radius.circular(110),
                                      bottom: Radius.circular(24),
                                    ),
                                    boxShadow: [
                                      BoxShadow(
                                        color: Colors.black.withValues(alpha: 0.04),
                                        blurRadius: 30,
                                        offset: const Offset(0, 8),
                                      ),
                                    ],
                                    border: Border.all(
                                      color: AppColors.outlineVariant.withValues(alpha: 0.25),
                                    ),
                                  ),
                                  child: ClipRRect(
                                    borderRadius: const BorderRadius.vertical(
                                      top: Radius.circular(110),
                                      bottom: Radius.circular(24),
                                    ),
                                    child: Stack(
                                      fit: StackFit.expand,
                                      children: [
                                        Image.asset(
                                          'assets/images/welcome_botanical.png',
                                          fit: BoxFit.cover,
                                          errorBuilder: (context, error, stackTrace) => Container(
                                            color: AppColors.secondaryContainer.withValues(alpha: 0.3),
                                            child: const Icon(
                                              Icons.eco,
                                              size: 56,
                                              color: AppColors.primarySage,
                                            ),
                                          ),
                                        ),
                                        // Gentle gradient overlay
                                        Container(
                                          decoration: BoxDecoration(
                                            gradient: LinearGradient(
                                              begin: Alignment.bottomCenter,
                                              end: Alignment.topCenter,
                                              colors: [
                                                AppColors.surface.withValues(alpha: 0.5),
                                                Colors.transparent,
                                              ],
                                            ),
                                          ),
                                        ),
                                        // Delicate organic leaf motif pill
                                        Positioned(
                                          bottom: 12,
                                          left: 0,
                                          right: 0,
                                          child: Center(
                                            child: Container(
                                              width: 32,
                                              height: 32,
                                              decoration: BoxDecoration(
                                                color: AppColors.surfaceContainerLowest
                                                    .withValues(alpha: 0.9),
                                                shape: BoxShape.circle,
                                                boxShadow: [
                                                  BoxShadow(
                                                    color: Colors.black.withValues(alpha: 0.06),
                                                    blurRadius: 4,
                                                  ),
                                                ],
                                              ),
                                              child: const Icon(
                                                Icons.spa,
                                                size: 17,
                                                color: AppColors.primarySage,
                                              ),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 24),

                          // Empathetic Headline
                          ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 320),
                            child: Text(
                              'You are safe to begin at your own pace.',
                              textAlign: TextAlign.center,
                              style: Theme.of(context).textTheme.displayMedium?.copyWith(
                                    fontSize: 25,
                                    height: 33 / 25,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.onSurface,
                                    letterSpacing: -0.3,
                                  ),
                            ),
                          ),
                          const SizedBox(height: 12),

                          // Grounding Message
                          ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 320),
                            child: const Text(
                              'Take your time. We are here to listen and connect you with human care whenever you feel ready.',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 14.5,
                                height: 23 / 14.5,
                                color: AppColors.onSurfaceVariant,
                                fontWeight: FontWeight.w400,
                              ),
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 24),

                      // 3. Focused Action Area
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            // Prominent Tactile Sage CTA
                            SizedBox(
                              width: double.infinity,
                              height: 54,
                              child: FilledButton(
                                style: FilledButton.styleFrom(
                                  backgroundColor: AppColors.primaryContainer,
                                  foregroundColor: AppColors.onPrimary,
                                  elevation: 2,
                                  shadowColor: AppColors.primary.withValues(alpha: 0.25),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                ),
                                onPressed: () => context.go(RoutePaths.languageSelection),
                                child: const Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Text(
                                      'Begin When Ready',
                                      style: TextStyle(
                                        fontSize: 15,
                                        fontWeight: FontWeight.w600,
                                        letterSpacing: 0.1,
                                      ),
                                    ),
                                    SizedBox(width: 8),
                                    Icon(Icons.arrow_forward, size: 19),
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),

                            // Subtle Terracotta Helpline Link
                            InkWell(
                              onTap: () => _showHelplineDialog(context),
                              borderRadius: BorderRadius.circular(8),
                              child: const Padding(
                                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                child: Wrap(
                                  alignment: WrapAlignment.center,
                                  crossAxisAlignment: WrapCrossAlignment.center,
                                  children: [
                                    Text(
                                      'Need to speak right now? ',
                                      style: TextStyle(
                                        fontSize: 13,
                                        color: AppColors.onSurfaceVariant,
                                      ),
                                    ),
                                    Text(
                                      'Call Emergency (112)',
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: FontWeight.w600,
                                        color: AppColors.tertiary,
                                        decoration: TextDecoration.underline,
                                        decorationColor: AppColors.tertiaryFixedDim,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
