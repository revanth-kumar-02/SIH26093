import '../../features/auth/pages/email_verification_page.dart';
import '../../features/auth/pages/forgot_password_page.dart';
import '../../features/auth/pages/login_page.dart';
import '../../features/auth/pages/sign_up_page.dart';
import '../../features/responder/data/services/responder_api_service.dart';
import '../../features/responder/pages/admin_views.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../features/responder/pages/ai_assessment_page.dart';
import '../../features/responder/pages/case_details_page.dart';
import '../../features/responder/pages/case_history_page.dart';
import '../../features/responder/pages/case_list_page.dart';
import '../../features/responder/pages/recommended_intervention_page.dart';
import '../../features/responder/pages/responder_dashboard_page.dart';
import '../../features/responder/pages/responder_login_page.dart';
import '../../features/responder/pages/svi_risk_page.dart';
import '../../features/victim/pages/ai_chat_page.dart';
import '../../features/victim/pages/assessment_status_page.dart';
import '../../features/victim/pages/consent_page.dart';
import '../../features/victim/pages/home_page.dart';
import '../../features/victim/pages/language_selection_page.dart';
import '../../features/victim/pages/splash_page.dart';
import '../../features/victim/pages/support_emergency_page.dart';
import '../../features/victim/pages/voice_interaction_page.dart';
import '../../features/victim/pages/welcome_page.dart';
import '../services/app_state_service.dart';
import '../services/supabase_auth_service.dart';
import 'route_paths.dart';

/// Application router configuration using GoRouter.
///
/// Provides route guards for:
/// - Supabase authentication and email verification state
/// - RBAC role authorization (PEOPLE vs ADMIN)
/// - Victim consent requirement
class AppRouter {
  AppRouter._();

  static final GoRouter router = GoRouter(
    initialLocation: RoutePaths.splash,
    debugLogDiagnostics: false,
    refreshListenable: Listenable.merge([
      AppStateService.instance,
      SupabaseAuthService.instance,
    ]),
    redirect: (context, state) {
      final path = state.matchedLocation;
      final auth = SupabaseAuthService.instance;
      final consent = AppStateService.instance.consentAgreed;

      // 1. Email Verification Guard: If signed up but unverified, enforce verification screen
      if (auth.status == AuthStatus.unverified && path != RoutePaths.verifyEmail && path != RoutePaths.splash) {
        return RoutePaths.verifyEmail;
      }

      // 2. Admin Route Guards: Enforce ADMIN role
      if (path.startsWith('/admin') && path != RoutePaths.adminLogin) {
        final hasAdminAuth = auth.isAdmin || 
            (ResponderApiService.instance.isAuthenticated && ResponderApiService.instance.session?.role == 'ADMIN');
        if (!hasAdminAuth) {
          return RoutePaths.adminLogin;
        }
      }

      // 3. Responder Route Guards
      if (path.startsWith('/responder') && path != RoutePaths.responderLogin) {
        final hasAdminAuth = auth.isAdmin || ResponderApiService.instance.isAuthenticated;
        if (!hasAdminAuth) {
          return RoutePaths.responderLogin;
        }
      }

      // 4. Victim Consent Guard: Screens requiring completed consent
      const consentGuarded = [
        RoutePaths.home,
        RoutePaths.aiChat,
        RoutePaths.voiceInteraction,
        RoutePaths.assessmentStatus,
        RoutePaths.supportEmergency,
      ];

      final isOnboardingDone = auth.onboardingCompleted || consent;
      if (!isOnboardingDone && consentGuarded.contains(path)) {
        if (auth.preferredLanguage == null || auth.preferredLanguage!.isEmpty) {
          debugPrint('[ROUTER] Routing to LANGUAGE');
          return RoutePaths.languageSelection;
        } else if (!auth.consentAccepted) {
          debugPrint('[ROUTER] Routing to CONSENT');
          return RoutePaths.consent;
        }
      }

      return null;
    },
    routes: [
      // ── Authentication Flow ───────────────────────────────────
      GoRoute(
        path: RoutePaths.login,
        name: 'login',
        builder: (context, state) => const LoginPage(),
      ),
      GoRoute(
        path: RoutePaths.register,
        name: 'register',
        builder: (context, state) => const SignUpPage(),
      ),
      GoRoute(
        path: RoutePaths.verifyEmail,
        name: 'verifyEmail',
        builder: (context, state) => const EmailVerificationPage(),
      ),
      GoRoute(
        path: RoutePaths.forgotPassword,
        name: 'forgotPassword',
        builder: (context, state) => const ForgotPasswordPage(),
      ),

      // ── Victim Flow ───────────────────────────────────────────
      GoRoute(
        path: RoutePaths.splash,
        name: 'splash',
        builder: (context, state) => const SplashPage(),
      ),
      GoRoute(
        path: RoutePaths.welcome,
        name: 'welcome',
        builder: (context, state) => const WelcomePage(),
      ),
      GoRoute(
        path: RoutePaths.languageSelection,
        name: 'languageSelection',
        builder: (context, state) => const LanguageSelectionPage(),
      ),
      GoRoute(
        path: RoutePaths.consent,
        name: 'consent',
        builder: (context, state) => const ConsentPage(),
      ),
      GoRoute(
        path: RoutePaths.home,
        name: 'home',
        builder: (context, state) => const HomePage(),
      ),
      GoRoute(
        path: RoutePaths.aiChat,
        name: 'aiChat',
        builder: (context, state) => const AiChatPage(),
      ),
      GoRoute(
        path: RoutePaths.voiceInteraction,
        name: 'voiceInteraction',
        builder: (context, state) => const VoiceInteractionPage(),
      ),
      GoRoute(
        path: RoutePaths.assessmentStatus,
        name: 'assessmentStatus',
        builder: (context, state) => const AssessmentStatusPage(),
      ),
      GoRoute(
        path: RoutePaths.supportEmergency,
        name: 'supportEmergency',
        builder: (context, state) => const SupportEmergencyPage(),
      ),

      // ── Admin Flow (Phase 11) ──────────────────────────────────────────────────
      GoRoute(
        path: RoutePaths.adminLogin,
        name: 'adminLogin',
        builder: (context, state) => const ResponderLoginPage(),
      ),
      GoRoute(
        path: RoutePaths.adminDashboard,
        name: 'adminDashboard',
        builder: (context, state) => const AdminDashboardPage(),
      ),
      GoRoute(
        path: RoutePaths.adminCases,
        name: 'adminCases',
        builder: (context, state) => const AdminCasesPage(),
      ),
      GoRoute(
        path: RoutePaths.adminCaseDetails,
        name: 'adminCaseDetails',
        builder: (context, state) {
          final caseId = state.pathParameters['caseId'] ?? '';
          return AdminCaseDetailPage(caseId: caseId);
        },
      ),
      GoRoute(
        path: RoutePaths.adminAssessments,
        name: 'adminAssessments',
        builder: (context, state) => const AdminCasesPage(),
      ),
      GoRoute(
        path: RoutePaths.adminSviRisk,
        name: 'adminSviRisk',
        builder: (context, state) => const AdminDashboardPage(),
      ),
      GoRoute(
        path: RoutePaths.adminRecommendations,
        name: 'adminRecommendations',
        builder: (context, state) => const AdminCasesPage(),
      ),
      GoRoute(
        path: RoutePaths.adminAudit,
        name: 'adminAudit',
        builder: (context, state) => const AdminAuditPage(),
      ),
      GoRoute(
        path: RoutePaths.adminSettings,
        name: 'adminSettings',
        builder: (context, state) => const AdminSettingsPage(),
      ),

      // ── Responder Flow ────────────────────────────────────────
      GoRoute(
        path: RoutePaths.responderLogin,
        name: 'responderLogin',
        builder: (context, state) => const ResponderLoginPage(),
      ),
      GoRoute(
        path: RoutePaths.responderDashboard,
        name: 'responderDashboard',
        builder: (context, state) => const ResponderDashboardPage(),
      ),
      GoRoute(
        path: RoutePaths.responderCaseList,
        name: 'responderCaseList',
        builder: (context, state) => const CaseListPage(),
      ),
      GoRoute(
        path: RoutePaths.responderCaseDetails,
        name: 'responderCaseDetails',
        builder: (context, state) {
          final caseId = state.pathParameters['caseId'] ?? 'unknown';
          return CaseDetailsPage(caseId: caseId);
        },
      ),
      GoRoute(
        path: RoutePaths.responderAiAssessment,
        name: 'responderAiAssessment',
        builder: (context, state) => const AiAssessmentPage(),
      ),
      GoRoute(
        path: RoutePaths.responderSviRisk,
        name: 'responderSviRisk',
        builder: (context, state) => const SviRiskPage(),
      ),
      GoRoute(
        path: RoutePaths.responderIntervention,
        name: 'responderIntervention',
        builder: (context, state) => const RecommendedInterventionPage(),
      ),
      GoRoute(
        path: RoutePaths.responderCaseHistory,
        name: 'responderCaseHistory',
        builder: (context, state) => const CaseHistoryPage(),
      ),
    ],

    // ── Error page ──────────────────────────────────────────────
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Page Not Found')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text(
              'The requested page could not be found.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 24),
            FilledButton.tonal(
              onPressed: () => context.go(RoutePaths.splash),
              child: const Text('Go Home'),
            ),
          ],
        ),
      ),
    ),
  );
}
