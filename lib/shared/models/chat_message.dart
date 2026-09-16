class ChatMessage {
  final String id;
  final String text;
  final bool isAssistant;
  final String timestamp;
  final bool isSystemReassurance;
  final String inputSource; // 'text' or 'voice'

  const ChatMessage({
    required this.id,
    required this.text,
    required this.isAssistant,
    required this.timestamp,
    this.isSystemReassurance = false,
    this.inputSource = 'text',
  });
}
