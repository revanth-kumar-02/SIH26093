import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/ai_assessment_page.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/case_history_page.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/case_list_page.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/recommended_intervention_page.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/responder_dashboard_page.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/responder_login_page.dart';
import 'package:nhaa_stress_assessment/features/responder/pages/svi_risk_page.dart';

Widget createTestableWidget(Widget child) {
  return MaterialApp(
    home: child,
  );
}

void main() {
  group('Responder Portal Screen Tests', () {
    testWidgets('ResponderLoginPage renders credentials inputs and action button', (tester) async {
      await tester.pumpWidget(createTestableWidget(const ResponderLoginPage()));
      expect(find.text('Responder Login'), findsOneWidget);
      expect(find.byType(TextFormField), findsNWidgets(2));
      expect(find.text('Authenticate & Access Portal'), findsOneWidget);
    });

    testWidgets('ResponderDashboardPage renders operational title and cards', (tester) async {
      await tester.pumpWidget(createTestableWidget(const ResponderDashboardPage()));
      await tester.pump();
      expect(find.text('NHAA 14566 — Operational Triage Dashboard'), findsOneWidget);
    });

    testWidgets('CaseListPage renders queue title and search field', (tester) async {
      await tester.pumpWidget(createTestableWidget(const CaseListPage()));
      await tester.pump();
      expect(find.text('Case Management Queue'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('SviRiskPage renders deterministic SVI formula information', (tester) async {
      await tester.pumpWidget(createTestableWidget(const SviRiskPage()));
      expect(find.text('Stress Vulnerability Index (SVI) Formula'), findsOneWidget);
      expect(find.textContaining('Deterministic SVI v1.0 Scoring Model'), findsOneWidget);
    });

    testWidgets('AiAssessmentPage renders multimodal AI assessment architecture', (tester) async {
      await tester.pumpWidget(createTestableWidget(const AiAssessmentPage()));
      expect(find.text('AI Multimodal Assessment Insights'), findsOneWidget);
      expect(find.textContaining('IndicConformer Multilingual ASR'), findsOneWidget);
    });

    testWidgets('RecommendedInterventionPage renders support pathways and decision workflow', (tester) async {
      await tester.pumpWidget(createTestableWidget(const RecommendedInterventionPage()));
      expect(find.text('Support Pathways & Intervention Engine'), findsOneWidget);
      expect(find.textContaining('7 Support Categories'), findsOneWidget);
    });

    testWidgets('CaseHistoryPage renders append-only audit trail governance', (tester) async {
      await tester.pumpWidget(createTestableWidget(const CaseHistoryPage()));
      expect(find.text('Audit History & Governance'), findsOneWidget);
      expect(find.textContaining('append-only security standards'), findsOneWidget);
    });
  });
}
