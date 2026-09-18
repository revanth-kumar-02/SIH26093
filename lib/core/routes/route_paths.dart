/// Centralized route path constants.
///
/// All route paths are defined here to avoid scattered magic strings.
/// Grouped by user flow: victim-facing and responder-facing.
class RoutePaths {
  RoutePaths._();

  // ── Authentication Flow ─────────────────────────────────────────
  static const String login = '/login';
  static const String register = '/register';
  static const String verifyEmail = '/verify-email';
  static const String forgotPassword = '/forgot-password';

  // ── Victim Flow ─────────────────────────────────────────────────
  static const String splash = '/';
  static const String welcome = '/welcome';
  static const String languageSelection = '/language';
  static const String consent = '/consent';
  static const String home = '/home';
  static const String aiChat = '/chat';
  static const String voiceInteraction = '/voice';
  static const String assessmentStatus = '/assessment-status';
  static const String supportEmergency = '/support';

  // ── Admin Flow (Phase 11) ──────────────────────────────────────────────────
  static const String adminLogin = '/admin/login';
  static const String adminDashboard = '/admin/dashboard';
  static const String adminCases = '/admin/cases';
  static const String adminCaseDetails = '/admin/cases/:caseId';
  static const String adminAssessments = '/admin/assessments';
  static const String adminSviRisk = '/admin/svi';
  static const String adminRecommendations = '/admin/recommendations';
  static const String adminAudit = '/admin/audit';
  static const String adminSettings = '/admin/settings';

  // ── Responder Flow ──────────────────────────────────────────────
  static const String responderLogin = '/responder/login';
  static const String responderDashboard = '/responder/dashboard';
  static const String responderCaseList = '/responder/cases';
  static const String responderCaseDetails = '/responder/cases/:caseId';
  static const String responderAiAssessment = '/responder/assessment';
  static const String responderSviRisk = '/responder/svi-risk';
  static const String responderIntervention = '/responder/intervention';
  static const String responderCaseHistory = '/responder/history';
}
