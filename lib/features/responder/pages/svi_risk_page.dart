import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen 16: SVI / Risk Details Page
/// Explains the deterministic Stress Vulnerability Index (SVI v1.0) formula, factor weights, and triage bands.
class SviRiskPage extends StatelessWidget {
  const SviRiskPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Stress Vulnerability Index (SVI) Formula'),
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
                            Icon(Icons.functions, color: AppColors.primary, size: 24),
                            SizedBox(width: 10),
                            Text('Deterministic SVI v1.0 Scoring Model', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          ],
                        ),
                        Divider(height: 24),
                        Text(
                          'SVI is computed independently of generative tokens using the formula:\n\n'
                          'Factor Contribution = Weight × Presence × Confidence × Evidence Strength\n'
                          'SVI = min(100.0, max(0.0, sum(Factor Contributions)))\n\n'
                          'Triage Risk Bands:\n'
                          '• LOW: 0.0 – 29.9\n'
                          '• MODERATE: 30.0 – 59.9\n'
                          '• HIGH: 60.0 – 84.9\n'
                          '• CRITICAL: 85.0 – 100.0\n\n'
                          'Safety Overrides:\n'
                          'Active physical danger or suicidal distress triggers immediate safety alerts regardless of numerical score.',
                          style: TextStyle(fontSize: 13, height: 1.5),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                FilledButton.tonal(
                  onPressed: () => context.go(RoutePaths.responderCaseList),
                  child: const Text('Return to Active Case Queue'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
