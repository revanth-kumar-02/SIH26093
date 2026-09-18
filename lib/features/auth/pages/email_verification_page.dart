import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/supabase_auth_service.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen: Email Verification Required
///
/// Prompts newly registered users to verify their email address before accessing
/// the protected Sanctuary platform.
class EmailVerificationPage extends StatefulWidget {
  const EmailVerificationPage({super.key});

  @override
  State<EmailVerificationPage> createState() => _EmailVerificationPageState();
}

class _EmailVerificationPageState extends State<EmailVerificationPage> {
  bool _isChecking = false;
  bool _isResending = false;
  String? _statusMessage;
  bool _isError = false;

  Future<void> _checkVerification() async {
    setState(() {
      _isChecking = true;
      _statusMessage = null;
      _isError = false;
    });

    final auth = SupabaseAuthService.instance;
    final verified = await auth.refreshVerificationStatus();

    if (!mounted) return;

    setState(() {
      _isChecking = false;
    });

    if (verified) {
      if (auth.isAdmin) {
        context.go(RoutePaths.adminDashboard);
      } else {
        context.go(RoutePaths.welcome);
      }
    } else {
      setState(() {
        _isError = true;
        _statusMessage = 'Email not yet verified. Please check your inbox and click the verification link.';
      });
    }
  }

  Future<void> _resendVerification() async {
    final email = SupabaseAuthService.instance.email;
    if (email == null || email.isEmpty) {
      setState(() {
        _isError = true;
        _statusMessage = 'Unable to determine email. Please return to login.';
      });
      return;
    }

    setState(() {
      _isResending = true;
      _statusMessage = null;
      _isError = false;
    });

    final success = await SupabaseAuthService.instance.resendVerificationEmail(email);

    if (!mounted) return;

    setState(() {
      _isResending = false;
      if (success) {
        _isError = false;
        _statusMessage = 'A fresh verification email has been sent to $email.';
      } else {
        _isError = true;
        _statusMessage = SupabaseAuthService.instance.errorMessage ?? 'Failed to resend verification email.';
      }
    });
  }

  Future<void> _handleSignOut() async {
    await SupabaseAuthService.instance.signOut();
    if (mounted) {
      context.go(RoutePaths.login);
    }
  }

  @override
  Widget build(BuildContext context) {
    final email = SupabaseAuthService.instance.email ?? 'your registered email';

    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Verification Icon
                  Center(
                    child: Container(
                      width: 76,
                      height: 76,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: AppColors.secondaryContainer.withValues(alpha: 0.5),
                        border: Border.all(
                          color: AppColors.primarySage.withValues(alpha: 0.3),
                          width: 1.5,
                        ),
                      ),
                      child: const Icon(
                        Icons.mark_email_unread_outlined,
                        size: 38,
                        color: AppColors.primary,
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Title
                  Text(
                    'Verify your email',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          fontSize: 25,
                          fontWeight: FontWeight.w600,
                          color: AppColors.onSurface,
                          letterSpacing: -0.4,
                        ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),

                  // Description
                  Text(
                    'We sent a verification link to:\n$email',
                    style: const TextStyle(
                      fontSize: 14.5,
                      color: Color(0xFF575E58),
                      height: 1.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Please click the link in your email to activate your account and access TrueVoice.',
                    style: TextStyle(
                      fontSize: 13,
                      color: AppColors.surfaceMutedText,
                      height: 1.4,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),

                  // Feedback Banner
                  if (_statusMessage != null) ...[
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: _isError
                            ? AppColors.tertiaryFixed.withValues(alpha: 0.4)
                            : AppColors.primaryFixed.withValues(alpha: 0.3),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: _isError
                              ? AppColors.tertiary.withValues(alpha: 0.4)
                              : AppColors.primarySage.withValues(alpha: 0.4),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            _isError ? Icons.info_outline : Icons.check_circle_outline,
                            color: _isError ? AppColors.tertiary : AppColors.primary,
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _statusMessage!,
                              style: TextStyle(
                                color: _isError ? AppColors.tertiary : AppColors.primary,
                                fontSize: 12.5,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 18),
                  ],

                  // Continue / Verify Button (48dp height)
                  SizedBox(
                    height: 48,
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: _isChecking ? null : _checkVerification,
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.primaryContainer,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        elevation: 0,
                      ),
                      child: _isChecking
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                            )
                          : const Text(
                              "I've verified my email / Continue",
                              style: TextStyle(
                                fontSize: 14.5,
                                fontWeight: FontWeight.w600,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Resend Verification Button (48dp height)
                  SizedBox(
                    height: 48,
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: _isResending ? null : _resendVerification,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.primary,
                        side: BorderSide(color: AppColors.primarySage.withValues(alpha: 0.5)),
                        padding: const EdgeInsets.symmetric(horizontal: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: _isResending
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.primary),
                            )
                          : const Text(
                              'Resend verification email',
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Sign Out / Return to Login
                  Center(
                    child: TextButton(
                      onPressed: _handleSignOut,
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.secondaryOlive,
                      ),
                      child: const Text(
                        'Back to Sign In',
                        style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w500),
                      ),
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
