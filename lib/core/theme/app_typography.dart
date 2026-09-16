import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Centralized typography definitions matching the Stitch design specifications.
///
/// Uses:
/// - Plus Jakarta Sans for headlines / titles
/// - Inter for body, labels, and metadata
class AppTypography {
  AppTypography._();

  /// Build the [TextTheme] for the given [colorScheme].
  static TextTheme textTheme(ColorScheme colorScheme) {
    final Color defaultColor = colorScheme.onSurface;

    return TextTheme(
      // ── Headline / Display (Plus Jakarta Sans) ───────────────────
      displayLarge: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 32,
        height: 40 / 32,
        letterSpacing: -0.64, // -0.02em
        color: defaultColor,
      ),
      displayMedium: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 26,
        height: 34 / 26,
        letterSpacing: -0.26, // -0.01em
        color: defaultColor,
      ),
      displaySmall: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 24,
        height: 32 / 24,
        letterSpacing: -0.24,
        color: defaultColor,
      ),

      headlineLarge: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 24,
        height: 32 / 24,
        letterSpacing: -0.24,
        color: defaultColor,
      ),
      headlineMedium: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 21,
        height: 28 / 21,
        letterSpacing: -0.21,
        color: defaultColor,
      ),
      headlineSmall: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 19,
        height: 26 / 19,
        color: defaultColor,
      ),

      titleLarge: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 19,
        height: 26 / 19,
        color: defaultColor,
      ),
      titleMedium: GoogleFonts.plusJakartaSans(
        fontWeight: FontWeight.w600,
        fontSize: 16,
        height: 22 / 16,
        color: defaultColor,
      ),
      titleSmall: GoogleFonts.inter(
        fontWeight: FontWeight.w600,
        fontSize: 15,
        height: 20 / 15,
        color: defaultColor,
      ),

      // ── Body (Inter) ─────────────────────────────────────────────
      bodyLarge: GoogleFonts.inter(
        fontWeight: FontWeight.w400,
        fontSize: 17,
        height: 26 / 17,
        color: defaultColor,
      ),
      bodyMedium: GoogleFonts.inter(
        fontWeight: FontWeight.w400,
        fontSize: 15,
        height: 24 / 15,
        color: defaultColor,
      ),
      bodySmall: GoogleFonts.inter(
        fontWeight: FontWeight.w400,
        fontSize: 13,
        height: 20 / 13,
        color: colorScheme.onSurfaceVariant,
      ),

      // ── Label (Inter) ────────────────────────────────────────────
      labelLarge: GoogleFonts.inter(
        fontWeight: FontWeight.w600,
        fontSize: 15,
        height: 20 / 15,
        color: defaultColor,
      ),
      labelMedium: GoogleFonts.inter(
        fontWeight: FontWeight.w500,
        fontSize: 13,
        height: 18 / 13,
        color: defaultColor,
      ),
      labelSmall: GoogleFonts.inter(
        fontWeight: FontWeight.w500,
        fontSize: 11,
        height: 16 / 11,
        letterSpacing: 0.22, // 0.02em
        color: colorScheme.onSurfaceVariant,
      ),
    );
  }
}
