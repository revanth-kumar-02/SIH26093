class IntakeDraft {
  final String type; // 'voice' or 'text'
  final String previewText;
  final int durationSeconds;
  final DateTime updatedAt;

  const IntakeDraft({
    required this.type,
    required this.previewText,
    this.durationSeconds = 0,
    required this.updatedAt,
  });

  String get timeAgo {
    final diff = DateTime.now().difference(updatedAt);
    if (diff.inSeconds < 60) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}
