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
    // Authoritative Supabase Project URL for TrueVoice (sih26093)
    return 'https://wcuhsdhyyhdfglejcgcu.supabase.co';
  }

  /// Resolves the active Supabase Anon Key.
  static String get anonKey {
    if (customAnonKey != null && customAnonKey!.isNotEmpty) {
      return customAnonKey!;
    }
    if (_envAnonKey.isNotEmpty) {
      return _envAnonKey;
    }
    // Authoritative Supabase Public Anon Key
    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndjdWhzZGh5eWhkZmdsZWpjZ2N1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk3MTU0MzIsImV4cCI6MjEwNTI5MTQzMn0.miFb_sgZZOjuGFXR_vpneT4fRtlPTE6I4ZaC7tItiJU';
  }

  /// Whether Supabase credentials are configured.
  static bool get isConfigured => url.isNotEmpty && anonKey.isNotEmpty;
}
