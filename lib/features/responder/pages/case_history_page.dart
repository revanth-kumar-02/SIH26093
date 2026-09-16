import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen 18: Case History / Audit Trail Standalone Page
class CaseHistoryPage extends StatelessWidget {
  const CaseHistoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Audit History & Governance'),
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
                            Icon(Icons.history_edu, color: AppColors.primary, size: 24),
                            SizedBox(width: 10),
                            Text('Audit Trail Governance', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                          ],
                        ),
                        Divider(height: 24),
                        Text(
                          'The NHAA audit framework adheres to append-only security standards:\n\n'
                          '• Every responder view, assignment, status update, and recommendation decision is immutably logged.\n'
                          '• High privacy guardrails: raw microphone audio and plaintext passwords are never stored in audit logs.\n'
                          '• Full provenance: Modified recommendations preserve both the original AI recommendation and the responder note.',
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
