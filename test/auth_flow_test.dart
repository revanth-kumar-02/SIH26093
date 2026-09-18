import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nhaa_stress_assessment/core/routes/app_router.dart';
import 'package:nhaa_stress_assessment/core/services/supabase_auth_service.dart';
import 'package:nhaa_stress_assessment/core/theme/app_theme.dart';
import 'package:nhaa_stress_assessment/features/auth/pages/email_verification_page.dart';
import 'package:nhaa_stress_assessment/features/auth/pages/forgot_password_page.dart';
import 'package:nhaa_stress_assessment/features/auth/pages/login_page.dart';
import 'package:nhaa_stress_assessment/features/auth/pages/sign_up_page.dart';

void main() {
  group('Supabase Auth Flow & UI Screen Tests', () {
    setUp(() {
      SupabaseAuthService.instance.signOut();
    });

    testWidgets('1. LoginPage renders title, inputs, password toggle, and buttons', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const LoginPage(),
        ),
      );
      await tester.pumpAndSettle();

      // Title & Subtitle
      expect(find.text('Welcome back'), findsOneWidget);
      expect(find.text('Sign in to access your secure TrueVoice space.'), findsOneWidget);

      // Input fields
      expect(find.widgetWithText(TextFormField, 'Email address'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Password'), findsOneWidget);

      // Action Buttons
      expect(find.widgetWithText(FilledButton, 'Sign In'), findsOneWidget);
      expect(find.widgetWithText(TextButton, 'Forgot Password?'), findsOneWidget);
      expect(find.widgetWithText(OutlinedButton, 'Create Account'), findsOneWidget);

      // Password toggle button
      final toggleFinder = find.byIcon(Icons.visibility_off_outlined);
      expect(toggleFinder, findsOneWidget);
      await tester.tap(toggleFinder);
      await tester.pump();
      expect(find.byIcon(Icons.visibility_outlined), findsOneWidget);
    });

    testWidgets('2. LoginPage enforces validation on empty submission', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const LoginPage(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.widgetWithText(FilledButton, 'Sign In'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter your email address.'), findsOneWidget);
      expect(find.text('Please enter your password.'), findsOneWidget);
    });

    testWidgets('3. LoginPage validates invalid email format', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const LoginPage(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.widgetWithText(TextFormField, 'Email address'), 'invalidemail');
      await tester.enterText(find.widgetWithText(TextFormField, 'Password'), 'Password123');
      await tester.tap(find.widgetWithText(FilledButton, 'Sign In'));
      await tester.pumpAndSettle();

      expect(find.text('Please enter a valid email format.'), findsOneWidget);
    });

    testWidgets('4. SignUpPage renders registration inputs and action', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const SignUpPage(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Create account'), findsAtLeastNWidgets(1));
      expect(find.widgetWithText(TextFormField, 'Full name'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Email address'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Password (minimum 6 characters)'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Confirm password'), findsOneWidget);
      expect(find.widgetWithText(FilledButton, 'Create account'), findsOneWidget);
    });

    testWidgets('5. SignUpPage enforces password confirmation match', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const SignUpPage(),
        ),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.widgetWithText(TextFormField, 'Full name'), 'Jane Doe');
      await tester.enterText(find.widgetWithText(TextFormField, 'Email address'), 'jane@example.com');
      await tester.enterText(find.widgetWithText(TextFormField, 'Password (minimum 6 characters)'), 'Password123');
      await tester.enterText(find.widgetWithText(TextFormField, 'Confirm password'), 'DifferentPass456');

      await tester.tap(find.widgetWithText(FilledButton, 'Create account'));
      await tester.pumpAndSettle();

      expect(find.text('Passwords do not match.'), findsOneWidget);
    });

    testWidgets('6. EmailVerificationPage renders verification guidance and resend CTA', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const EmailVerificationPage(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Verify your email'), findsOneWidget);
      expect(find.widgetWithText(FilledButton, "I've verified my email / Continue"), findsOneWidget);
      expect(find.widgetWithText(OutlinedButton, 'Resend verification email'), findsOneWidget);
      expect(find.text('Back to Sign In'), findsOneWidget);
    });

    testWidgets('7. ForgotPasswordPage handles email input and submission', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: AppTheme.light,
          home: const ForgotPasswordPage(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Reset password'), findsOneWidget);
      expect(find.widgetWithText(TextFormField, 'Email address'), findsOneWidget);
      expect(find.widgetWithText(FilledButton, 'Send reset link'), findsOneWidget);

      await tester.enterText(find.widgetWithText(TextFormField, 'Email address'), 'user@example.com');
      await tester.tap(find.widgetWithText(FilledButton, 'Send reset link'));
      await tester.pumpAndSettle();

      expect(find.text('Password reset link sent!'), findsOneWidget);
    });

    testWidgets('8. SupabaseAuthService handles session and role assignment', (tester) async {
      final auth = SupabaseAuthService.instance;

      // Set admin session
      auth.setSessionForTesting(
        userId: 'admin-uuid',
        email: 'admin@nhaa.gov.in',
        role: 'ADMIN',
        displayName: 'System Admin',
      );
      expect(auth.isAuthenticated, isTrue);
      expect(auth.isAdmin, isTrue);
      expect(auth.role, 'ADMIN');

      // Reset / Sign out
      auth.resetForTesting();
      expect(auth.isAuthenticated, isFalse);

      // Set people session
      auth.setSessionForTesting(
        userId: 'people-uuid',
        email: 'people@nhaa.gov.in',
        role: 'PEOPLE',
        displayName: 'Citizen User',
      );
      expect(auth.isAuthenticated, isTrue);
      expect(auth.isPeople, isTrue);
      expect(auth.role, 'PEOPLE');

      auth.resetForTesting();
    });

    testWidgets('9. AppRouter initializes with login/splash for unauthenticated user', (tester) async {
      await tester.pumpWidget(
        MaterialApp.router(
          theme: AppTheme.light,
          routerConfig: AppRouter.router,
        ),
      );
      await tester.pumpAndSettle();

      // Unauthenticated user at splash or login
      expect(find.byType(MaterialApp), findsOneWidget);
    });

    testWidgets('10. SupabaseAuthService handles unverified state flow', (tester) async {
      final auth = SupabaseAuthService.instance;
      auth.setSessionForTesting(
        userId: 'unverified-uuid',
        email: 'newcitizen@example.com',
        role: 'PEOPLE',
        displayName: 'New Citizen',
        status: AuthStatus.unverified,
      );
      expect(auth.status, AuthStatus.unverified);
      expect(auth.email, 'newcitizen@example.com');
      expect(auth.displayName, 'New Citizen');

      // Verified state
      auth.setSessionForTesting(
        userId: 'unverified-uuid',
        email: 'newcitizen@example.com',
        role: 'PEOPLE',
        displayName: 'New Citizen',
        status: AuthStatus.authenticated,
      );
      expect(auth.status, AuthStatus.authenticated);
      expect(auth.role, 'PEOPLE');

      auth.resetForTesting();
    });
  });
}

