import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nhaa_stress_assessment/features/responder/data/models/responder_models.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/admin_shell_layout.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/admin_views.dart';

Widget createTestableWidget(Widget child) {
  return MaterialApp(
    home: child,
  );
}

void main() {
  group('Admin Web Dashboard & Shell Layout Tests', () {
    testWidgets('AdminShellLayout renders sidebar navigation and project identity', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(
        createTestableWidget(
          const AdminShellLayout(
            currentPath: '/admin/dashboard',
            title: 'Overview',
            breadcrumb: 'Admin / Overview',
            child: Center(child: Text('Dashboard Content Body')),
          ),
        ),
      );

      expect(find.text('NHAA 14566'), findsOneWidget);
      expect(find.text('Admin Operations'), findsOneWidget);
      expect(find.text('Overview'), findsNWidgets(2)); // Title and Sidebar nav item
      expect(find.text('Cases'), findsOneWidget);
      expect(find.text('Assessments'), findsOneWidget);
      expect(find.text('SVI & Risk'), findsOneWidget);
      expect(find.text('Recommendations'), findsOneWidget);
      expect(find.text('Audit Log'), findsOneWidget);
      expect(find.text('Settings'), findsOneWidget);
      expect(find.text('Dashboard Content Body'), findsOneWidget);
      expect(find.text('DEMO / SYNTHETIC DATA'), findsOneWidget);
    });

    testWidgets('AdminDashboardPage initial state displays loading indicator', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(createTestableWidget(const AdminDashboardPage()));
      expect(find.text('Loading cases...'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('AdminCasesPage renders search field and filter dropdowns', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(createTestableWidget(const AdminCasesPage()));
      expect(find.byType(TextField), findsOneWidget);
      expect(find.text('Filter'), findsOneWidget);
    });

    testWidgets('AdminAuditPage renders audit header and shell', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(createTestableWidget(const AdminAuditPage()));
      expect(find.text('Audit Log'), findsNWidgets(2));
    });

    testWidgets('AdminSettingsPage renders strict two-role model confirmation', (tester) async {
      tester.view.physicalSize = const Size(1200, 800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);

      await tester.pumpWidget(createTestableWidget(const AdminSettingsPage()));
      expect(find.text('Role Configuration (LOCKED)'), findsOneWidget);
      expect(find.text('1. PEOPLE'), findsOneWidget);
      expect(find.text('2. ADMIN'), findsOneWidget);
      expect(find.textContaining('ai4bharat/indic-conformer-600m-multilingual'), findsOneWidget);
      expect(find.textContaining('google/gemma-3n-E2B-it'), findsOneWidget);
    });

    test('DashboardAnalyticsModel JSON parsing test', () {
      final json = {
        "active_cases": 12,
        "urgent_review": 2,
        "high_risk": 4,
        "pending_reviews": 6,
        "risk_distribution": {
          "LOW": 3,
          "MODERATE": 4,
          "HIGH": 4,
          "CRITICAL": 1
        },
        "requires_attention_cases": [],
        "recent_cases": []
      };

      final model = DashboardAnalyticsModel.fromJson(json);
      expect(model.activeCases, 12);
      expect(model.urgentReview, 2);
      expect(model.highRisk, 4);
      expect(model.pendingReviews, 6);
      expect(model.riskDistribution['LOW'], 3);
      expect(model.riskDistribution['CRITICAL'], 1);
    });

    test('AdminAuditItemModel JSON parsing test', () {
      final json = {
        "id": "audit-1234",
        "timestamp": "2026-09-16T15:21:00Z",
        "actor": "ADMIN",
        "actor_id": "admin-1",
        "actor_type": "ADMIN",
        "event": "RECOMMENDATION_MODIFIED",
        "entity": "RECOMMENDATION",
        "entity_id": "rec-99",
        "case_reference": "NHAA-2026-SYN-0812",
        "case_id": "case-uuid-1",
        "details": {"decision": "MODIFY", "note": "Adjusted action"}
      };

      final model = AdminAuditItemModel.fromJson(json);
      expect(model.id, "audit-1234");
      expect(model.actorType, "ADMIN");
      expect(model.event, "RECOMMENDATION_MODIFIED");
      expect(model.caseReference, "NHAA-2026-SYN-0812");
      expect(model.details["decision"], "MODIFY");
    });
  });
}
