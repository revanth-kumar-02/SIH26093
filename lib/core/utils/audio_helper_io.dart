import 'dart:io';

Future<String> getAudioTempPath() async {
  final tempDir = Directory.systemTemp;
  return '${tempDir.path}/voice_${DateTime.now().millisecondsSinceEpoch}.wav';
}

Future<List<int>?> readAudioBytesAndDelete(String path) async {
  if (path.isEmpty) return null;
  final file = File(path);
  if (await file.exists()) {
    final bytes = await file.readAsBytes();
    try {
      await file.delete();
    } catch (_) {}
    return bytes;
  }
  return null;
}
