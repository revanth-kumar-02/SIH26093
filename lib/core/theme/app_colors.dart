import 'package:flutter/material.dart';

/// Centralized color palette for TrueVoice.
///
/// Authoritative tokens directly derived from the approved Stitch designs:
/// - Sage Green: Primary (#335941 / #4B7258)
/// - Warm Ivory: Main Background (#F8FAF6)
/// - Soft Olive: Secondary (#596244 / #6E7758)
/// - Deep Charcoal: Text (#191C1A / #222523)
/// - Muted Terracotta/Coral: Emergency Accent (#8B3627 / #AA4D3D)
class AppColors {
  AppColors._();

  // ── Primary (Sage Green) ─────────────────────────────────────────
  static const Color primary = Color(0xFF335941);
  static const Color primarySage = Color(0xFF4B7258);
  static const Color primaryContainer = Color(0xFF4B7258);
  static const Color onPrimary = Color(0xFFFFFFFF);
  static const Color onPrimaryContainer = Color(0xFFC9F5D4);
  static const Color primaryFixed = Color(0xFFC2EDCD);
  static const Color primaryFixedDim = Color(0xFFA6D1B2);
  static const Color onPrimaryFixed = Color(0xFF002110);
  static const Color onPrimaryFixedVariant = Color(0xFF284E37);

  // ── Secondary (Soft Olive) ───────────────────────────────────────
  static const Color secondary = Color(0xFF596244);
  static const Color secondaryOlive = Color(0xFF6E7758);
  static const Color secondaryContainer = Color(0xFFDDE7C1);
  static const Color onSecondary = Color(0xFFFFFFFF);
  static const Color onSecondaryContainer = Color(0xFF5F684A);
  static const Color secondaryFixed = Color(0xFFDDE7C1);
  static const Color secondaryFixedDim = Color(0xFFC1CBA7);
  static const Color onSecondaryFixed = Color(0xFF171E07);
  static const Color onSecondaryFixedVariant = Color(0xFF424A2E);

  // ── Tertiary (Muted Terracotta / Crisis Accent) ──────────────────
  static const Color tertiary = Color(0xFF8B3627);
  static const Color tertiaryContainer = Color(0xFFAA4D3D);
  static const Color tertiaryFixed = Color(0xFFFFDAD4);
  static const Color tertiaryFixedDim = Color(0xFFFFB4A6);
  static const Color onTertiary = Color(0xFFFFFFFF);
  static const Color onTertiaryContainer = Color(0xFFFFE4DF);
  static const Color onTertiaryFixed = Color(0xFF3F0300);
  static const Color onTertiaryFixedVariant = Color(0xFF7D2C1E);

  // ── Surfaces & Warm Ivory Backgrounds ────────────────────────────
  static const Color background = Color(0xFFF8FAF6);
  static const Color onBackground = Color(0xFF191C1A);
  static const Color surface = Color(0xFFF8FAF6);
  static const Color onSurface = Color(0xFF191C1A);
  static const Color onSurfaceVariant = Color(0xFF414942);
  static const Color surfaceMutedText = Color(0xFF575E58);

  static const Color surfaceContainerLowest = Color(0xFFFFFFFF);
  static const Color surfaceContainerLow = Color(0xFFF3F4F0);
  static const Color surfaceContainer = Color(0xFFEDEEEB);
  static const Color surfaceContainerHigh = Color(0xFFE7E9E5);
  static const Color surfaceContainerHighest = Color(0xFFE1E3DF);
  static const Color surfaceDim = Color(0xFFD9DAD7);
  static const Color surfaceBright = Color(0xFFF8FAF6);

  // ── Outline & Dividers ───────────────────────────────────────────
  static const Color outline = Color(0xFF727972);
  static const Color outlineVariant = Color(0xFFC1C8C0);

  // ── Error & Alert ────────────────────────────────────────────────
  static const Color error = Color(0xFFBA1A1A);
  static const Color errorContainer = Color(0xFFFFDAD6);
  static const Color onError = Color(0xFFFFFFFF);
  static const Color onErrorContainer = Color(0xFF93000A);

  // ── Status Indicators ────────────────────────────────────────────
  static const Color statusSafe = Color(0xFF4B7258);
  static const Color statusLow = Color(0xFF6E7758);
  static const Color statusModerate = Color(0xFFD97706);
  static const Color statusHigh = Color(0xFFC2410C);
  static const Color statusCritical = Color(0xFF8B3627);

  /// Generates the Stitch-aligned light [ColorScheme].
  static ColorScheme get lightColorScheme => const ColorScheme(
        brightness: Brightness.light,
        primary: primary,
        onPrimary: onPrimary,
        primaryContainer: primaryContainer,
        onPrimaryContainer: onPrimaryContainer,
        secondary: secondary,
        onSecondary: onSecondary,
        secondaryContainer: secondaryContainer,
        onSecondaryContainer: onSecondaryContainer,
        tertiary: tertiary,
        onTertiary: onTertiary,
        tertiaryContainer: tertiaryContainer,
        onTertiaryContainer: onTertiaryContainer,
        error: error,
        onError: onError,
        errorContainer: errorContainer,
        onErrorContainer: onErrorContainer,
        surface: surface,
        onSurface: onSurface,
        onSurfaceVariant: onSurfaceVariant,
        outline: outline,
        outlineVariant: outlineVariant,
        surfaceContainerLowest: surfaceContainerLowest,
        surfaceContainerLow: surfaceContainerLow,
        surfaceContainer: surfaceContainer,
        surfaceContainerHigh: surfaceContainerHigh,
        surfaceContainerHighest: surfaceContainerHighest,
      );

  /// Generates a calm dark [ColorScheme].
  static ColorScheme get darkColorScheme => ColorScheme.fromSeed(
        seedColor: primary,
        secondary: secondary,
        tertiary: tertiary,
        error: error,
        brightness: Brightness.dark,
        surface: const Color(0xFF191C1A),
      );
}
