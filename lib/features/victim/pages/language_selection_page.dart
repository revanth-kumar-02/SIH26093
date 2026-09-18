import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/app_state_service.dart';
import '../../../../core/services/supabase_auth_service.dart';
import '../../../../core/theme/app_colors.dart';

class LanguageItem {
  const LanguageItem({
    required this.code,
    required this.name,
    required this.nativeName,
    required this.subtext,
  });

  final String code;
  final String name;
  final String nativeName;
  final String subtext;
}

/// Screen 3: Language Selection — Source of Truth from Stitch.
///
/// Enables victims to choose their most comfortable language with native script
/// rendering, audio preview capabilities, and immediate visual confirmation.
class LanguageSelectionPage extends StatefulWidget {
  const LanguageSelectionPage({super.key});

  @override
  State<LanguageSelectionPage> createState() => _LanguageSelectionPageState();
}

class _LanguageSelectionPageState extends State<LanguageSelectionPage> {
  late String _selectedLanguage = AppStateService.instance.selectedLanguage;
  String? _playingAudioLang;

  static const List<LanguageItem> _languages = [
    LanguageItem(
      code: 'en',
      name: 'English',
      nativeName: 'English',
      subtext: 'English • Primary',
    ),
    LanguageItem(
      code: 'hi',
      name: 'Hindi',
      nativeName: 'हिन्दी',
      subtext: 'आपकी सहजता ही प्राथमिकता है',
    ),
    LanguageItem(
      code: 'ta',
      name: 'Tamil',
      nativeName: 'தமிழ்',
      subtext: 'நாங்கள் உங்களுக்கு உதவ இங்கே இருக்கிறோம்',
    ),
    LanguageItem(
      code: 'te',
      name: 'Telugu',
      nativeName: 'తెలుగు',
      subtext: 'మీ భద్రత మరియు గోప్యత మా బాధ్యత',
    ),
    LanguageItem(
      code: 'kn',
      name: 'Kannada',
      nativeName: 'ಕನ್ನಡ',
      subtext: 'ನಿಮ್ಮ ಹಿತರಕ್ಷಣೆ ನಮ್ಮ ಆದ್ಯತೆ',
    ),
    LanguageItem(
      code: 'ml',
      name: 'Malayalam',
      nativeName: 'മലയാളം',
      subtext: 'ഞങ്ങൾ നിങ്ങളുടെ കൂടെയുണ്ട്',
    ),
  ];

  void _playAudioSample(String langName) {
    setState(() => _playingAudioLang = langName);
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.volume_up, color: Colors.white, size: 20),
            const SizedBox(width: 10),
            Expanded(child: Text('Playing sample voice prompt in $langName...')),
          ],
        ),
        backgroundColor: AppColors.primary,
        duration: const Duration(milliseconds: 1400),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
    Future.delayed(const Duration(milliseconds: 1400), () {
      if (mounted && _playingAudioLang == langName) {
        setState(() => _playingAudioLang = null);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.onSurface),
          onPressed: () => context.go(RoutePaths.welcome),
        ),
        title: const Text(
          'Choose Language',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: AppColors.onSurface,
          ),
        ),
        centerTitle: false,
        actions: [
          Container(
            margin: const EdgeInsets.only(right: 16),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.surfaceContainerLow,
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.shield_outlined, size: 14, color: AppColors.primary),
                SizedBox(width: 4),
                Text(
                  'Private & safe',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: AppColors.onSurfaceVariant),
                ),
              ],
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 430),
            child: Column(
              children: [
                // Top Reassurance Banner
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                    decoration: BoxDecoration(
                      color: AppColors.surfaceContainerLow,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.translate, size: 20, color: AppColors.primary),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Choose the language in which you feel most comfortable speaking or typing.',
                            style: TextStyle(
                              fontSize: 13,
                              height: 1.4,
                              color: AppColors.onSurfaceVariant,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // Language Cards List
                Expanded(
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                    itemCount: _languages.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final item = _languages[index];
                      final isSelected = _selectedLanguage == item.name;
                      final isPlaying = _playingAudioLang == item.name;

                      return InkWell(
                        onTap: () => setState(() => _selectedLanguage = item.name),
                        borderRadius: BorderRadius.circular(14),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? AppColors.surfaceContainerLowest
                                : AppColors.surfaceContainerLow.withValues(alpha: 0.6),
                            borderRadius: BorderRadius.circular(14),
                            border: Border.all(
                              color: isSelected
                                  ? AppColors.primary.withValues(alpha: 0.6)
                                  : AppColors.outlineVariant.withValues(alpha: 0.3),
                              width: isSelected ? 1.5 : 1,
                            ),
                            boxShadow: isSelected
                                ? [
                                    BoxShadow(
                                      color: AppColors.primary.withValues(alpha: 0.06),
                                      blurRadius: 10,
                                      offset: const Offset(0, 3),
                                    ),
                                  ]
                                : null,
                          ),
                          child: Row(
                            children: [
                              // Left Radio Check Indicator
                              Container(
                                width: 26,
                                height: 26,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: isSelected
                                      ? AppColors.primary
                                      : AppColors.surfaceContainer,
                                ),
                                child: isSelected
                                    ? const Icon(Icons.check, size: 16, color: Colors.white)
                                    : null,
                              ),
                              const SizedBox(width: 14),

                              // Language Titles
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Text(
                                          item.nativeName,
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w600,
                                            color: AppColors.onSurface,
                                          ),
                                        ),
                                        if (item.name != item.nativeName) ...[
                                          const SizedBox(width: 6),
                                          Text(
                                            '(${item.name})',
                                            style: const TextStyle(
                                              fontSize: 13,
                                              color: AppColors.onSurfaceVariant,
                                            ),
                                          ),
                                        ],
                                        if (isSelected) ...[
                                          const SizedBox(width: 8),
                                          Container(
                                            padding: const EdgeInsets.symmetric(
                                              horizontal: 8,
                                              vertical: 2,
                                            ),
                                            decoration: BoxDecoration(
                                              color: AppColors.primary.withValues(alpha: 0.12),
                                              borderRadius: BorderRadius.circular(999),
                                            ),
                                            child: const Text(
                                              'Selected',
                                              style: TextStyle(
                                                fontSize: 11,
                                                fontWeight: FontWeight.w600,
                                                color: AppColors.primary,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ],
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      item.subtext,
                                      style: const TextStyle(
                                        fontSize: 12.5,
                                        color: AppColors.onSurfaceVariant,
                                      ),
                                    ),
                                  ],
                                ),
                              ),

                              // Audio Preview Button
                              IconButton(
                                icon: Icon(
                                  isPlaying ? Icons.graphic_eq : Icons.volume_up,
                                  color: isPlaying ? AppColors.primary : AppColors.secondary,
                                  size: 22,
                                ),
                                onPressed: () => _playAudioSample(item.name),
                                tooltip: 'Listen to sample in ${item.name}',
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),

                // Bottom Action Button
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  child: SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: FilledButton(
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        elevation: 2,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      onPressed: () async {
                        await SupabaseAuthService.instance.saveLanguage(_selectedLanguage);
                        if (context.mounted) {
                          debugPrint('[ROUTER] Routing to CONSENT');
                          context.go(RoutePaths.consent);
                        }
                      },
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            'Confirm & Continue',
                            style: TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          SizedBox(width: 8),
                          Icon(Icons.arrow_forward, size: 19),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
