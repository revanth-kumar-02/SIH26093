import 'package:http/http.dart' as http;

Future<String> getAudioTempPath() async {
  return '';
}

Future<List<int>?> readAudioBytesAndDelete(String path) async {
  if (path.isEmpty) return null;
  try {
    final res = await http.get(Uri.parse(path));
    return res.bodyBytes;
  } catch (_) {
    return null;
  }
}
