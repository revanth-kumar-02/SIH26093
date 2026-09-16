import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen 15: AI Assessment Page
/// Deep-dive view of multimodal evidence extracted by Gemma 3n E2B IT.
class AiAssessmentPage extends StatelessWidget {
  const AiAssessmentPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('AI Multimodal Assessment Insights'),
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
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.psychology, color: AppColors.primary, size: 24),
                            SizedBox(width: 10),
                            Text(
                              'Multimodal AI Assessment Architecture',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const Divider(height: 24),
                        const Text(
                          'The AI assessment pipeline synthesizes three independent signal streams:\n'
                          '1. IndicConformer Multilingual ASR (22 Indian Languages)\n'
                          '2. Speech Emotion Recognition (Wav2Vec2 7-class distribution)\n'
                          '3. Text Emotion & MentalBERT Stress Detection (Dreaddit classifier)\n\n'
                          'Gemma 3n E2B IT produces structured clinical observations without direct score generation. Scores are computed exclusively by the deterministic SVI Engine.',
                          style: TextStyle(fontSize: 14, height: 1.5),
                        ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.surfaceContainerLowest,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.primary.withValues(alpha: 0.2)),
                          ),
                          child: const Row(
                            children: [
                              Icon(Icons.verified_user_outlined, color: AppColors.primary, size: 20),
                              SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Explainable, transparent, and auditable triage intelligence.',
                                  style: TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.w600),
                                ),
                              ),
                            ],
                          ),
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
