import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen 17: Recommended Intervention Standalone Page
class RecommendedInterventionPage extends StatelessWidget {
  const RecommendedInterventionPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Support Pathways & Intervention Engine'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go(RoutePaths.responderDashboard),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 800),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Card(
                  elevation: 2,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  color: Colors.white,
                  child: const Padding(
                    padding: EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.shield, color: AppColors.primary, size: 24),
                            SizedBox(width: 10),
                            Text('Support Pathways & Decision Workflow', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          ],
                        ),
                        Divider(height: 24),
                        Text(
                          '7 Support Categories:\n'
                          '1. Counselling & Psychosocial\n'
                          '2. Legal Aid & Rights Advisory\n'
                          '3. Medical Assistance Referral\n'
                          '4. Safety & Protection Protocol\n'
                          '5. Police Assistance Review (Strictly Human Responder Decision)\n'
                          '6. Emergency Support Escalation\n'
                          '7. Social & Community Support\n\n'
                          'Zero Autonomous External Dispatch:\n'
                          'All recommendations require human responder verification before external action.',
                          style: TextStyle(fontSize: 13, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                FilledButton.tonal(
                  onPressed: () => context.go(RoutePaths.responderCaseList),
                  child: const Text('Review Active Case Recommendations'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
