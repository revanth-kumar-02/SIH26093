import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'api_config.dart';
import 'api_exceptions.dart';

/// Central HTTP API Client managing serialization, timeouts, and network error handling.
class ApiClient {
  final http.Client _httpClient;

  ApiClient({http.Client? httpClient}) : _httpClient = httpClient ?? http.Client();

  Map<String, String> get _defaultHeaders => {
        'Content-Type': 'application/json; charset=UTF-8',
        'Accept': 'application/json',
      };

  Future<Map<String, dynamic>> get(String url) async {
    try {
      final uri = Uri.parse(url);
      final response = await _httpClient
          .get(uri, headers: _defaultHeaders)
          .timeout(ApiConfig.timeoutDuration);

      return _handleResponse(response);
    } on TimeoutException {
      throw const RequestTimeoutException();
    } on SocketException catch (e) {
      throw NetworkConnectionException(technicalDetails: e.message);
    } on http.ClientException catch (e) {
      throw NetworkConnectionException(technicalDetails: e.message);
    } on FormatException catch (e) {
      throw InvalidResponseException(technicalDetails: e.message);
    }
  }

  Future<Map<String, dynamic>> post(String url, {Map<String, dynamic>? body}) async {
    return _postWithTimeout(url, body: body, timeout: ApiConfig.timeoutDuration);
  }

  /// POST with an explicit timeout — use for chat messages (AI inference is slow).
  Future<Map<String, dynamic>> postWithTimeout(
    String url, {
    Map<String, dynamic>? body,
    Duration timeout = ApiConfig.chatTimeoutDuration,
  }) async {
    return _postWithTimeout(url, body: body, timeout: timeout);
  }

  Future<Map<String, dynamic>> _postWithTimeout(
    String url, {
    Map<String, dynamic>? body,
    required Duration timeout,
  }) async {
    try {
      final uri = Uri.parse(url);
      final response = await _httpClient
          .post(
            uri,
            headers: _defaultHeaders,
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(timeout);

      return _handleResponse(response);
    } on TimeoutException {
      throw const RequestTimeoutException();
    } on SocketException catch (e) {
      throw NetworkConnectionException(technicalDetails: e.message);
    } on http.ClientException catch (e) {
      throw NetworkConnectionException(technicalDetails: e.message);
    } on FormatException catch (e) {
      throw InvalidResponseException(technicalDetails: e.message);
    }
  }

  Future<Map<String, dynamic>> postMultipart(
    String url, {
    required List<int> fileBytes,
    required String filename,
    required String fieldName,
    Map<String, String>? fields,
  }) async {
    try {
      final uri = Uri.parse(url);
      final request = http.MultipartRequest('POST', uri);
      if (fields != null) {
        request.fields.addAll(fields);
      }
      request.files.add(
        http.MultipartFile.fromBytes(
          fieldName,
          fileBytes,
          filename: filename,
        ),
      );

      final streamedResponse = await _httpClient
          .send(request)
          .timeout(const Duration(seconds: 25));
      final response = await http.Response.fromStream(streamedResponse);

      return _handleResponse(response);
    } on TimeoutException {
      throw const RequestTimeoutException();
    } on SocketException catch (e) {
      throw NetworkConnectionException(technicalDetails: e.message);
    } on http.ClientException catch (e) {
      throw NetworkConnectionException(technicalDetails: e.message);
    } on FormatException catch (e) {
      throw InvalidResponseException(technicalDetails: e.message);
    }
  }

  Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) return {};
      final dynamic decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) {
        return decoded;
      }
      return {'data': decoded};
    }

    if (response.statusCode == 404) {
      throw const SessionNotFoundException();
    }

    throw ServerErrorException(
      statusCode: response.statusCode,
      technicalDetails: response.body,
    );
  }

  void close() {
    _httpClient.close();
  }
}
