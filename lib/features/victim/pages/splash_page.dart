import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/supabase_auth_service.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen 1: Splash (Redesigned) — Source of Truth from Stitch.
///
/// Serene, trauma-informed splash screen with a gentle breathing halo,
/// product identity, and verified privacy status.
class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> with SingleTickerProviderStateMixin {
  late final AnimationController _breatheController;
  late final Animation<double> _scaleAnimation;
  late final Animation<double> _opacityAnimation;
  Timer? _navigationTimer;

  @override
  void initState() {
    super.initState();
    _breatheController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 4500),
    )..repeat(reverse: true);

    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.08).animate(
      CurvedAnimation(parent: _breatheController, curve: Curves.easeInOut),
    );

    _opacityAnimation = Tween<double>(begin: 0.45, end: 0.80).animate(
      CurvedAnimation(parent: _breatheController, curve: Curves.easeInOut),
    );

    // Transition to appropriate destination based on Supabase Auth state
    _navigationTimer = Timer(const Duration(milliseconds: 2600), () {
      if (mounted) {
        _proceedNow();
      }
    });
  }

  @override
  void dispose() {
    _navigationTimer?.cancel();
    _breatheController.dispose();
    super.dispose();
  }

  void _proceedNow() {
    _navigationTimer?.cancel();
    final auth = SupabaseAuthService.instance;
    if (auth.status == AuthStatus.unverified) {
      context.go(RoutePaths.verifyEmail);
    } else if (auth.isAuthenticated) {
      if (auth.isAdmin) {
        debugPrint('[ROUTER] Routing to ADMIN');
        context.go(RoutePaths.adminDashboard);
      } else if (auth.onboardingCompleted) {
        debugPrint('[ROUTER] Routing to HOME');
        context.go(RoutePaths.home);
      } else if (auth.preferredLanguage == null || auth.preferredLanguage!.isEmpty) {
        debugPrint('[ROUTER] Routing to LANGUAGE');
        context.go(RoutePaths.welcome);
      } else if (!auth.consentAccepted) {
        debugPrint('[ROUTER] Routing to CONSENT');
        context.go(RoutePaths.consent);
      } else {
        debugPrint('[ROUTER] Routing to HOME');
        context.go(RoutePaths.home);
      }
    } else {
      context.go(RoutePaths.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      body: GestureDetector(
        onTap: _proceedNow,
        behavior: HitTestBehavior.opaque,
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 430),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Top spacing
                    const SizedBox(height: 20),

                    // Central Visual & Typography
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        // Gentle Breathing Halo & Brand Emblem
                        Stack(
                          alignment: Alignment.center,
                          children: [
                            // Subtle organic breathing halo outer ring
                            AnimatedBuilder(
                              animation: _breatheController,
                              builder: (context, child) {
                                return Transform.scale(
                                  scale: _scaleAnimation.value,
                                  child: Container(
                                    width: 176,
                                    height: 176,
                                    decoration: BoxDecoration(
                                      shape: BoxShape.circle,
                                      color: const Color(0xFFE2EBE5).withValues(
                                        alpha: _opacityAnimation.value * 0.6,
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                            // Delicate border ring
                            Container(
                              width: 128,
                              height: 128,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                border: Border.all(
                                  color: AppColors.primarySage.withValues(alpha: 0.18),
                                  width: 1.2,
                                ),
                              ),
                            ),
                            // Emblem Container
                            Container(
                              width: 96,
                              height: 96,
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: const Color(0xFFF5F1E8),
                                border: Border.all(
                                  color: const Color(0xFFE3DDCF).withValues(alpha: 0.7),
                                  width: 1,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: const Color(0xFF4B7258).withValues(alpha: 0.08),
                                    blurRadius: 24,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: ClipOval(
                                child: Image.asset(
                                  'assets/images/truevoice_emblem.png',
                                  fit: BoxFit.contain,
                                  errorBuilder: (context, error, stackTrace) => const Icon(
                                    Icons.spa,
                                    color: AppColors.primarySage,
                                    size: 40,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 32),

                        // Product Identity
                        Text(
                          'TrueVoice',
                          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                                fontSize: 28,
                                fontWeight: FontWeight.w600,
                                color: const Color(0xFF222523),
                                letterSpacing: -0.5,
                              ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'Your voice matters.',
                          style: TextStyle(
                            fontSize: 15,
                            height: 1.6,
                            color: Color(0xFF575E58),
                            fontWeight: FontWeight.w400,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),

                    // Serene Minimalist Status Footer
                    Padding(
                      padding: const EdgeInsets.only(bottom: 32),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceContainerLow.withValues(alpha: 0.8),
                          borderRadius: BorderRadius.circular(999),
                          border: Border.all(
                            color: AppColors.outlineVariant.withValues(alpha: 0.4),
                          ),
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                              width: 8,
                              height: 8,
                              decoration: const BoxDecoration(
                                color: Color(0xFF4B7258),
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 8),
                            const Text(
                              'Secured & private',
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w500,
                                color: Color(0xFF575E58),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
