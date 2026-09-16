import 'package:flutter/material.dart';

/// Convenience extensions on [BuildContext] to reduce boilerplate
/// when accessing theme data, media queries, and navigator.
extension ContextExtensions on BuildContext {
  /// Access the current [ThemeData].
  ThemeData get theme => Theme.of(this);

  /// Access the current [ColorScheme].
  ColorScheme get colorScheme => theme.colorScheme;

  /// Access the current [TextTheme].
  TextTheme get textTheme => theme.textTheme;

  /// Access the current [MediaQueryData].
  MediaQueryData get mediaQuery => MediaQuery.of(this);

  /// Screen width.
  double get screenWidth => mediaQuery.size.width;

  /// Screen height.
  double get screenHeight => mediaQuery.size.height;

  /// Whether the screen is considered narrow (mobile-width).
  bool get isNarrowScreen => screenWidth < 600;

  /// Whether the screen is considered wide (desktop/tablet-width).
  bool get isWideScreen => screenWidth >= 1024;
}
