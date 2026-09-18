import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:supabase_flutter/supabase_flutter.dart';
import '../network/api_config.dart';

/// Authentication state categories for route guards and UI state presentation.
enum AuthStatus {
  initial,
  loading,
  unauthenticated,
  unverified,
  authenticated,
  error,
}

/// Centralized authentication and session management service using Supabase Auth.
///
/// Responsibilities:
/// - Supabase Auth credentials, sessions, and email verification checks
/// - JIT user profile synchronization with PostgreSQL via FastAPI
/// - Role-based authorization: PEOPLE vs ADMIN
/// - Session lifecycle, persistence, and token refresh
class SupabaseAuthService extends ChangeNotifier {
  static final SupabaseAuthService instance = SupabaseAuthService._internal();
  SupabaseAuthService._internal();

  AuthStatus _status = AuthStatus.initial;
  AuthStatus get status => _status;

  String? _userId;
  String? get userId => _userId;

  String? _email;
  String? get email => _email;

  String? _displayName;
  String? get displayName => _displayName;

  String _role = 'PEOPLE';
  String get role => _role;

  String? _accessToken;
  String? get accessToken => _accessToken;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  bool get isAuthenticated => _status == AuthStatus.authenticated && _accessToken != null;
  bool get isEmailVerified => _status == AuthStatus.authenticated;
  bool get isAdmin => isAuthenticated && _role.toUpperCase() == 'ADMIN';
  bool get isPeople => isAuthenticated && _role.toUpperCase() == 'PEOPLE';

  SupabaseClient? get _supabase {
    try {
      return Supabase.instance.client;
    } catch (_) {
      return null;
    }
  }

  /// Initialize auth state from existing session or local storage.
  Future<void> initialize() async {
    _status = AuthStatus.loading;
    notifyListeners();

    final client = _supabase;
    if (client == null) {
      // Local fallback mode when Supabase client is uninitialized (e.g. tests)
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      return;
    }

    try {
      final session = client.auth.currentSession;
      final user = client.auth.currentUser;

      if (session != null && user != null) {
        _userId = user.id;
        _email = user.email;
        _displayName = (user.userMetadata?['display_name'] ?? _email?.split('@').first) as String?;
        _accessToken = session.accessToken;

        // Check email verification status
        final isConfirmed = user.emailConfirmedAt != null;
        if (!isConfirmed) {
          _status = AuthStatus.unverified;
        } else {
          _status = AuthStatus.authenticated;
          await _syncWithFastApi();
        }
      } else {
        _status = AuthStatus.unauthenticated;
      }
    } catch (e) {
      _status = AuthStatus.unauthenticated;
      _errorMessage = e.toString();
    }

    // Listen to Supabase auth state changes
    try {
      client.auth.onAuthStateChange.listen((data) {
        _handleAuthStateChange(data.event, data.session);
      });
    } catch (_) {}

    notifyListeners();
  }

  void _handleAuthStateChange(AuthChangeEvent event, Session? session) {
    if (event == AuthChangeEvent.signedIn && session != null) {
      final user = session.user;
      _userId = user.id;
      _email = user.email;
      _displayName = (user.userMetadata?['display_name'] ?? _email?.split('@').first) as String?;
      _accessToken = session.accessToken;

      final isConfirmed = user.emailConfirmedAt != null;
      if (!isConfirmed) {
        _status = AuthStatus.unverified;
      } else {
        _status = AuthStatus.authenticated;
        _syncWithFastApi();
      }
      notifyListeners();
    } else if (event == AuthChangeEvent.signedOut) {
      _clearState();
      _status = AuthStatus.unauthenticated;
      notifyListeners();
    } else if (event == AuthChangeEvent.tokenRefreshed && session != null) {
      _accessToken = session.accessToken;
      notifyListeners();
    } else if (event == AuthChangeEvent.userUpdated && session != null) {
      final user = session.user;
      final isConfirmed = user.emailConfirmedAt != null;
      if (isConfirmed && _status == AuthStatus.unverified) {
        _status = AuthStatus.authenticated;
        _syncWithFastApi();
        notifyListeners();
      }
    }
  }

  /// Sign in with email and password via Supabase Auth.
  Future<bool> signIn({required String email, required String password}) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();

    final client = _supabase;
    if (client == null) {
      _status = AuthStatus.error;
      _errorMessage = 'Authentication service is unavailable. Please try again later.';
      notifyListeners();
      return false;
    }

    try {
      final response = await client.auth.signInWithPassword(
        email: email.trim(),
        password: password,
      );

      final session = response.session;
      final user = response.user;

      if (user == null || session == null) {
        _status = AuthStatus.error;
        _errorMessage = 'Incorrect email or password.';
        notifyListeners();
        return false;
      }

      _userId = user.id;
      _email = user.email;
      _displayName = (user.userMetadata?['display_name'] ?? user.userMetadata?['full_name'] ?? _email?.split('@').first) as String?;
      _accessToken = session.accessToken;

      final roleMeta = (user.userMetadata?['role'] as String?)?.toUpperCase();
      if (roleMeta == 'ADMIN' || _email?.toLowerCase() == 'admin@nhaa.gov.in') {
        _role = 'ADMIN';
      } else {
        _role = 'PEOPLE';
      }

      final isConfirmed = user.emailConfirmedAt != null;
      if (!isConfirmed) {
        _status = AuthStatus.unverified;
        notifyListeners();
        return false;
      }

      _status = AuthStatus.authenticated;
      await _syncWithFastApi();
      notifyListeners();
      return true;
    } on AuthException catch (e) {
      _status = AuthStatus.error;
      _errorMessage = _formatAuthException(e);
      notifyListeners();
      return false;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = _formatGenericError(e);
      notifyListeners();
      return false;
    }
  }

  /// Register a new account via Supabase Auth.
  Future<bool> signUp({
    required String name,
    required String email,
    required String password,
  }) async {
    _status = AuthStatus.loading;
    _errorMessage = null;
    notifyListeners();

    final client = _supabase;
    if (client == null) {
      // Mock / Offline test fallback
      _userId = 'mock-${DateTime.now().millisecondsSinceEpoch}';
      _email = email.trim();
      _displayName = name.trim();
      _role = 'PEOPLE';
      _status = AuthStatus.unverified;
      notifyListeners();
      return true;
    }

    try {
      final response = await client.auth.signUp(
        email: email.trim(),
        password: password,
        data: {
          'display_name': name.trim(),
          'full_name': name.trim(),
          'role': 'PEOPLE',
        },
      );

      final user = response.user;
      if (user == null) {
        _status = AuthStatus.error;
        _errorMessage = 'Registration failed. Please try again.';
        notifyListeners();
        return false;
      }

      _userId = user.id;
      _email = user.email;
      _displayName = name.trim();
      _role = 'PEOPLE';
      _accessToken = response.session?.accessToken;

      // Always require email verification post-registration
      _status = AuthStatus.unverified;
      notifyListeners();
      return true;
    } on AuthException catch (e) {
      _status = AuthStatus.error;
      _errorMessage = _formatAuthException(e);
      notifyListeners();
      return false;
    } catch (e) {
      _status = AuthStatus.error;
      _errorMessage = _formatGenericError(e);
      notifyListeners();
      return false;
    }
  }

  /// Request password reset email via Supabase Auth.
  Future<bool> sendPasswordResetEmail(String email) async {
    _errorMessage = null;
    final client = _supabase;
    if (client == null) {
      return true; // Mock success for test environments
    }

    try {
      await client.auth.resetPasswordForEmail(email.trim());
      return true;
    } on AuthException catch (e) {
      _errorMessage = _formatAuthException(e);
      notifyListeners();
      return false;
    } catch (e) {
      _errorMessage = _formatGenericError(e);
      notifyListeners();
      return false;
    }
  }

  /// Resend verification email to user.
  Future<bool> resendVerificationEmail(String email) async {
    _errorMessage = null;
    final client = _supabase;
    if (client == null) {
      return true;
    }

    try {
      await client.auth.resend(
        type: OtpType.signup,
        email: email.trim(),
      );
      return true;
    } on AuthException catch (e) {
      _errorMessage = _formatAuthException(e);
      notifyListeners();
      return false;
    } catch (e) {
      _errorMessage = _formatGenericError(e);
      notifyListeners();
      return false;
    }
  }

  String _formatAuthException(AuthException e) {
    final msg = e.message.toLowerCase();
    if (msg.contains('invalid login credentials') ||
        msg.contains('invalid credentials') ||
        msg.contains('invalid grant')) {
      return 'Incorrect email or password.';
    }
    if (msg.contains('email not confirmed') || msg.contains('unconfirmed')) {
      return 'Please verify your email before signing in.';
    }
    if (msg.contains('user already registered') ||
        msg.contains('already registered') ||
        msg.contains('already exists')) {
      return 'An account with this email already exists.';
    }
    if (msg.contains('rate limit') || msg.contains('over_email_send_rate_limit')) {
      return 'Email rate limit reached. Please wait a few moments before trying again.';
    }
    if (msg.contains('password should be at least')) {
      return 'Password must be at least 6 characters.';
    }
    if (msg.contains('email address') && msg.contains('invalid')) {
      return 'Please enter a valid email address.';
    }
    return e.message;
  }

  String _formatGenericError(dynamic e) {
    final s = e.toString().toLowerCase();
    if (s.contains('socketexception') ||
        s.contains('failed host lookup') ||
        s.contains('clientexception') ||
        s.contains('network') ||
        s.contains('connection refused') ||
        s.contains('handshakeexception') ||
        s.contains('os error')) {
      return 'Unable to connect right now. Please check your internet connection and try again.';
    }
    return 'Unable to connect to authentication service. Please try again.';
  }

  /// Check if the user has confirmed their email and update state.
  Future<bool> refreshVerificationStatus() async {
    final client = _supabase;
    if (client == null) {
      // In mock/test mode, confirm verification immediately on refresh
      _status = AuthStatus.authenticated;
      _accessToken ??= 'mock-token-${_userId ?? "00000000-0000-0000-0000-000000000002"}';
      await _syncWithFastApi();
      notifyListeners();
      return true;
    }

    try {
      final response = await client.auth.getUser();
      final user = response.user;
      if (user != null) {
        final isConfirmed = user.emailConfirmedAt != null;
        if (isConfirmed) {
          _status = AuthStatus.authenticated;
          _accessToken = client.auth.currentSession?.accessToken;
          await _syncWithFastApi();
          notifyListeners();
          return true;
        }
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Sign out from Supabase Auth and reset state.
  Future<void> signOut() async {
    try {
      await _supabase?.auth.signOut();
    } catch (_) {}
    _clearState();
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  void _clearState() {
    _userId = null;
    _email = null;
    _displayName = null;
    _role = 'PEOPLE';
    _accessToken = null;
    _errorMessage = null;
  }

  /// Synchronize authenticated Supabase identity with PostgreSQL via FastAPI.
  Future<void> _syncWithFastApi() async {
    if (_accessToken == null || _accessToken!.isEmpty) return;

    try {
      final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/auth/sync');
      final response = await http
          .post(
            uri,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer $_accessToken',
            },
            body: jsonEncode({
              'access_token': _accessToken,
              'display_name': _displayName,
            }),
          )
          .timeout(const Duration(seconds: 4));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _role = (data['role'] as String?)?.toUpperCase() ?? 'PEOPLE';
        _displayName = data['display_name'] as String? ?? _displayName;
      }
    } catch (_) {
      // Backend sync fallback: preserve local role if backend unreachable
    }
  }

  @visibleForTesting
  void setSessionForTesting({
    required String userId,
    required String email,
    required String role,
    String? displayName,
    String? token,
    AuthStatus status = AuthStatus.authenticated,
  }) {
    _userId = userId;
    _email = email;
    _role = role.toUpperCase();
    _displayName = displayName ?? email.split('@').first;
    _accessToken = token ?? 'test-token';
    _status = status;
    notifyListeners();
  }

  @visibleForTesting
  void resetForTesting() {
    _clearState();
    _status = AuthStatus.unauthenticated;
    _errorMessage = null;
    notifyListeners();
  }
}
