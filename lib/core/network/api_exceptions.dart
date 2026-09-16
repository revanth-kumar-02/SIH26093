/// Base exception class for API operations.
/// Exposes user-facing, calm, trauma-informed error messages without technical stack traces.
abstract class ApiException implements Exception {
  final String userMessage;
  final String? technicalDetails;

  const ApiException({
    required this.userMessage,
    this.technicalDetails,
  });

  @override
  String toString() => userMessage;
}

class NetworkConnectionException extends ApiException {
  const NetworkConnectionException({
    super.userMessage = "We couldn't connect right now. Please try again.",
    super.technicalDetails,
  });
}

class RequestTimeoutException extends ApiException {
  const RequestTimeoutException({
    super.userMessage = "Connection timed out. Please take your time and try again.",
    super.technicalDetails,
  });
}

class ServerErrorException extends ApiException {
  final int statusCode;

  const ServerErrorException({
    required this.statusCode,
    super.userMessage = "Support service is currently unavailable. Please try again in a moment.",
    super.technicalDetails,
  });
}

class SessionNotFoundException extends ApiException {
  const SessionNotFoundException({
    super.userMessage = "Your session has expired. Starting a fresh session for you.",
    super.technicalDetails,
  });
}

class InvalidResponseException extends ApiException {
  const InvalidResponseException({
    super.userMessage = "Unexpected response received. Please try again.",
    super.technicalDetails,
  });
}
