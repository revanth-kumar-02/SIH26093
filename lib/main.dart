import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'core/constants/app_strings.dart';
import 'core/network/api_config.dart';
import 'core/network/supabase_config.dart';
import 'core/routes/app_router.dart';
import 'core/services/app_state_service.dart';
import 'core/services/supabase_auth_service.dart';
import 'core/theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Supabase Auth client with graceful fallback for testing/offline environments
  try {
    if (SupabaseConfig.isConfigured) {
      await Supabase.initialize(
        url: SupabaseConfig.url,
        // ignore: deprecated_member_use
        anonKey: SupabaseConfig.anonKey,
      );
    }
  } catch (e) {
    debugPrint('Supabase initialization notice: $e');
  }

  // Initialize central authentication session state
  await SupabaseAuthService.instance.initialize();

  // Reset active chat to guarantee a fresh chat on app startup (Requirement 2 & 5)
  AppStateService.instance.startFreshChatSession();

  // Auto-discover active backend endpoint (USB reverse, LAN Wi-Fi, or emulator)
  ApiConfig.discoverBaseUrl();

  runApp(const NhaaApp());
}

/// Root application widget.
///
/// Configures Material 3 theming, routing, and top-level app settings.
/// All screens are reached through [AppRouter].
class NhaaApp extends StatelessWidget {
  const NhaaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      // ── Identity ────────────────────────────────────────────────
      title: AppStrings.appName,
      debugShowCheckedModeBanner: false,

      // ── Theme ───────────────────────────────────────────────────
      theme: AppTheme.light,
      darkTheme: AppTheme.dark,
      themeMode: ThemeMode.system,

      // ── Routing ─────────────────────────────────────────────────
      routerConfig: AppRouter.router,
    );
  }
}
