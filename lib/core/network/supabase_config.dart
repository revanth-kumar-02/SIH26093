/// Centralized configuration for Supabase Auth on the Flutter client.
///
/// Only public parameters (URL and anon key) are stored here.
/// Sensitive server keys (service_role, database passwords, JWT signing secrets)
/// are NEVER stored or exposed on the client.
class SupabaseConfig {
  SupabaseConfig._();

  /// Supabase project URL configurable via `--dart-define=SUPABASE_URL=...`
  static const String _envUrl = String.fromEnvironment('SUPABASE_URL');

  /// Supabase anon public key configurable via `--dart-define=SUPABASE_ANON_KEY=...`
  static const String _envAnonKey = String.fromEnvironment('SUPABASE_ANON_KEY');

  /// Runtime URL override if needed for testing.
  static String? customUrl;

  /// Runtime anon key override if needed for testing.
  static String? customAnonKey;

  /// Resolves the active Supabase URL.
  static String get url {
    if (customUrl != null && customUrl!.isNotEmpty) {
      return customUrl!;
    }
    if (_envUrl.isNotEmpty) {
      return _envUrl;
    }
    // Default development project URL
    return 'https://sih26093-auth.supabase.co';
  }

  /// Resolves the active Supabase Anon Key.
  static String get anonKey {
    if (customAnonKey != null && customAnonKey!.isNotEmpty) {
      return customAnonKey!;
    }
    if (_envAnonKey.isNotEmpty) {
      return _envAnonKey;
    }
    // Safe mock public anon key for dev testing
    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpaDI2MDkzIiwicm9sZSI6ImFub24iLCJpYXQiOjE2MDAwMDAwMDAsImV4cCI6MTkwMDAwMDAwMH0.sih26093_public_anon_key_dev';
  }

  /// Whether Supabase credentials are configured.
  static bool get isConfigured => url.isNotEmpty && anonKey.isNotEmpty;
}
