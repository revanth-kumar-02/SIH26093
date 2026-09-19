import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/consent_page.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/home_page.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/language_selection_page.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/welcome_page.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/ai_chat_page.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/voice_interaction_page.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/assessment_status_page.dart';
import 'package:nhaa_stress_assessment/features/victim/pages/support_emergency_page.dart';

void main() {
  Widget createTestWidget(Widget child) {
    return MaterialApp(
      home: child,
    );
  }

  setUp(() {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  testWidgets('WelcomePage renders key elements and CTA', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const WelcomePage()));
    await tester.pump();

    expect(find.text('You are safe to begin at your own pace.'), findsOneWidget);
    expect(find.text('Begin When Ready'), findsOneWidget);
    expect(find.text('112'), findsWidgets);
  });

  testWidgets('LanguageSelectionPage renders languages and selection', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const LanguageSelectionPage()));
    await tester.pump();

    expect(find.text('Choose Language'), findsOneWidget);
    expect(find.text('English'), findsWidgets);
    expect(find.text('हिन्दी'), findsOneWidget);
    expect(find.text('Confirm & Continue'), findsOneWidget);
  });

  testWidgets('ConsentPage renders 3 reassurance cards and gentle checkbox', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const ConsentPage()));
    await tester.pump();

    expect(find.text('Clear, trauma-informed care'), findsOneWidget);
    expect(find.text('Your pace, your boundaries'), findsOneWidget);
    expect(find.text('Assisting human responders'), findsOneWidget);
    expect(find.text('You hold the reins'), findsOneWidget);
    expect(find.text('I Understand & Continue'), findsOneWidget);
  });

  testWidgets('HomePage renders intake choices and crisis bar', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const HomePage()));
    await tester.pump();

    expect(find.text('Talk with us'), findsOneWidget);
    expect(find.text('Type it out'), findsOneWidget);
    expect(find.text('How would you like to share what happened?'), findsOneWidget);
  });

  testWidgets('AiChatPage renders guide avatar and prompt chips', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const AiChatPage()));
    await tester.pump();

    expect(find.text('TrueVoice Guide'), findsWidgets);
    expect(find.text('I have a friend I can stay with'), findsOneWidget);
  });

  testWidgets('VoiceInteractionPage renders timer and audio control actions', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const VoiceInteractionPage()));
    await tester.pump();

    expect(find.text('00:00'), findsOneWidget);
    expect(find.text('Done speaking'), findsOneWidget);
  });

  testWidgets('AssessmentStatusPage renders triage steps and progress', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const AssessmentStatusPage()));
    await tester.pump();

    expect(find.text('Supportive intake status'), findsOneWidget);
    expect(find.text('Human Advocates Lead Every Step'), findsOneWidget);
    expect(find.text('Proceed to Support Options'), findsOneWidget);
  });

  testWidgets('SupportEmergencyPage renders personalized support plan structure', (tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(createTestWidget(const SupportEmergencyPage()));
    await tester.pump();

    expect(find.text('Your Support Plan'), findsOneWidget);
    expect(find.text('What We Heard'), findsOneWidget);
  });
}
