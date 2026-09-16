import 'package:flutter/material.dart';

import 'core/constants/app_strings.dart';
import 'core/routes/app_router.dart';
import 'core/theme/app_theme.dart';

void main() {
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
