import 'package:flutter_test/flutter_test.dart';
import 'package:nhaa_stress_assessment/main.dart';

void main() {
  testWidgets('App renders without crashing and shows TrueVoice', (tester) async {
    await tester.pumpWidget(const NhaaApp());
    await tester.pump();

    // Verify the splash page renders with the authoritative brand name
    expect(find.text('TrueVoice'), findsOneWidget);
    expect(find.text('Secured & private'), findsOneWidget);
  });
}
