import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/supabase_auth_service.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen: Login ("Welcome back")
///
/// Grounded, serene authentication interface strictly adhering to the Sanctuary design palette:
/// - Warm Ivory background (#F8FAF6)
/// - Sage Green primary (#335941 / #4B7258)
/// - Soft Olive secondary (#596244)
/// - Deep Charcoal text (#191C1A)
/// - Muted Terracotta alert accents (#8B3627)
class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleSignIn() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final auth = SupabaseAuthService.instance;
    final success = await auth.signIn(
      email: _emailController.text.trim(),
      password: _passwordController.text,
    );

    if (!mounted) return;

    setState(() {
      _isLoading = false;
    });

    if (success) {
      if (auth.isAdmin) {
        context.go(RoutePaths.adminDashboard);
      } else {
        context.go(RoutePaths.welcome);
      }
    } else {
      if (auth.status == AuthStatus.unverified) {
        context.go(RoutePaths.verifyEmail);
      } else {
        setState(() {
          _errorMessage = auth.errorMessage ?? 'Authentication failed. Please verify your credentials.';
        });
      }
    }
  }

  void _quickFill(String email, String pass) {
    setState(() {
      _emailController.text = email;
      _passwordController.text = pass;
      _errorMessage = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Form(
                key: _formKey,
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Brand Icon / Emblem
                    Center(
                      child: Container(
                        width: 68,
                        height: 68,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: const Color(0xFFF3F6F1),
                          border: Border.all(
                            color: AppColors.primarySage.withValues(alpha: 0.2),
                            width: 1.2,
                          ),
                        ),
                        child: const Icon(
                          Icons.spa_rounded,
                          size: 34,
                          color: AppColors.primarySage,
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Title
                    Text(
                      'Welcome back',
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontSize: 26,
                            fontWeight: FontWeight.w600,
                            color: AppColors.onSurface,
                            letterSpacing: -0.4,
                          ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Sign in to access your secure TrueVoice space.',
                      style: TextStyle(
                        fontSize: 14,
                        color: Color(0xFF575E58),
                        height: 1.4,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 28),

                    // Error Message Banner (Muted Terracotta)
                    if (_errorMessage != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        decoration: BoxDecoration(
                          color: AppColors.tertiaryFixed.withValues(alpha: 0.4),
                          borderRadius: BorderRadius.circular(10),
                          border: Border.all(
                            color: AppColors.tertiary.withValues(alpha: 0.3),
                          ),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.info_outline, color: AppColors.tertiary, size: 18),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _errorMessage!,
                                style: const TextStyle(
                                  color: AppColors.tertiary,
                                  fontSize: 12.5,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                    ],

                    // Email Field
                    TextFormField(
                      controller: _emailController,
                      keyboardType: TextInputType.emailAddress,
                      textInputAction: TextInputAction.next,
                      style: const TextStyle(fontSize: 14.5, color: AppColors.onSurface),
                      decoration: InputDecoration(
                        labelText: 'Email address',
                        labelStyle: const TextStyle(fontSize: 14, color: AppColors.surfaceMutedText),
                        prefixIcon: const Icon(Icons.email_outlined, size: 20, color: AppColors.secondaryOlive),
                        filled: true,
                        fillColor: AppColors.surfaceContainerLowest,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.6)),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.6)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppColors.primarySage, width: 1.5),
                        ),
                      ),
                      validator: (val) {
                        if (val == null || val.trim().isEmpty) return 'Please enter your email address.';
                        if (!val.contains('@') && !val.contains('_')) return 'Please enter a valid email format.';
                        return null;
                      },
                    ),
                    const SizedBox(height: 14),

                    // Password Field
                    TextFormField(
                      controller: _passwordController,
                      obscureText: _obscurePassword,
                      textInputAction: TextInputAction.done,
                      onFieldSubmitted: (_) => _handleSignIn(),
                      style: const TextStyle(fontSize: 14.5, color: AppColors.onSurface),
                      decoration: InputDecoration(
                        labelText: 'Password',
                        labelStyle: const TextStyle(fontSize: 14, color: AppColors.surfaceMutedText),
                        prefixIcon: const Icon(Icons.lock_outline_rounded, size: 20, color: AppColors.secondaryOlive),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                            size: 20,
                            color: AppColors.surfaceMutedText,
                          ),
                          onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                        ),
                        filled: true,
                        fillColor: AppColors.surfaceContainerLowest,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.6)),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.6)),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: AppColors.primarySage, width: 1.5),
                        ),
                      ),
                      validator: (val) {
                        if (val == null || val.isEmpty) return 'Please enter your password.';
                        return null;
                      },
                    ),
                    const SizedBox(height: 8),

                    // Forgot Password Link
                    Align(
                      alignment: Alignment.centerRight,
                      child: TextButton(
                        onPressed: () => context.push(RoutePaths.forgotPassword),
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 4),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: const Text(
                          'Forgot Password?',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: AppColors.secondaryOlive,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 18),

                    // Sign In Button (48dp height)
                    SizedBox(
                      height: 48,
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: _isLoading ? null : _handleSignIn,
                        style: FilledButton.styleFrom(
                          backgroundColor: AppColors.primaryContainer,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                          elevation: 0,
                        ),
                        child: _isLoading
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                              )
                            : const Text(
                                'Sign In',
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w600,
                                  letterSpacing: 0.1,
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Create Account Button
                    SizedBox(
                      height: 48,
                      width: double.infinity,
                      child: OutlinedButton(
                        onPressed: () => context.push(RoutePaths.register),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.primary,
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          side: BorderSide(color: AppColors.primarySage.withValues(alpha: 0.5)),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: const Text(
                          'Create Account',
                          style: TextStyle(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Demo Synthetic Credentials for Quick Verification
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Quick Demo Access:',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.surfaceMutedText),
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 8,
                            runSpacing: 6,
                            children: [
                              ActionChip(
                                label: const Text('Admin Portal', style: TextStyle(fontSize: 11)),
                                avatar: const Icon(Icons.admin_panel_settings, size: 14, color: AppColors.primarySage),
                                backgroundColor: AppColors.surfaceContainerLowest,
                                side: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
                                onPressed: () => _quickFill('admin@nhaa.gov.in', 'AdminPassword@123'),
                              ),
                              ActionChip(
                                label: const Text('Citizen / Victim', style: TextStyle(fontSize: 11)),
                                avatar: const Icon(Icons.person, size: 14, color: AppColors.secondaryOlive),
                                backgroundColor: AppColors.surfaceContainerLowest,
                                side: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
                                onPressed: () => _quickFill('people@nhaa.gov.in', 'PeoplePassword@123'),
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
      ),
    );
  }
}
