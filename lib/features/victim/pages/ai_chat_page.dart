import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/services/app_state_service.dart';
import '../../../../core/theme/app_colors.dart';

/// Screen 6: AI Chat — Source of Truth from Stitch.
///
/// Serene, trauma-informed conversational intake module with empathetic pacing,
/// reassurance dividers, prompt suggestions, grounding breathing exercise, and input controls.
class AiChatPage extends StatefulWidget {
  const AiChatPage({super.key});

  @override
  State<AiChatPage> createState() => _AiChatPageState();
}

class _AiChatPageState extends State<AiChatPage> {
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isListening = false;

  static const List<String> _promptSuggestions = [
    'I have a friend I can stay with',
    'I need safe shelter tonight',
    'Report anonymously',
    'I need legal advice',
  ];

  @override
  void initState() {
    super.initState();
    AppStateService.instance.addListener(_onStateChanged);
  }

  void _onStateChanged() {
    if (mounted) {
      setState(() {});
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scrollController.hasClients) {
          _scrollController.animateTo(
            _scrollController.position.maxScrollExtent,
            duration: const Duration(milliseconds: 300),
            curve: Curves.easeOut,
          );
        }
      });
    }
  }

  @override
  void dispose() {
    AppStateService.instance.removeListener(_onStateChanged);
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage([String? presetText]) {
    final text = presetText ?? _textController.text.trim();
    if (text.isEmpty) return;

    AppStateService.instance.sendUserMessage(text);
    if (presetText == null) _textController.clear();
  }

  void _showBreathingModal() {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 10),
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.secondaryContainer.withValues(alpha: 0.6),
              ),
              child: const Icon(Icons.self_improvement, size: 40, color: AppColors.primary),
            ),
            const SizedBox(height: 20),
            const Text(
              'Grounding Moment',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600, color: AppColors.onSurface),
            ),
            const SizedBox(height: 8),
            const Text(
              'Inhale gently for 4 seconds...\nHold for 4 seconds...\nExhale slowly for 4 seconds.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, height: 1.6, color: AppColors.onSurfaceVariant),
            ),
            const SizedBox(height: 20),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () => Navigator.of(ctx).pop(),
              child: const Text('I Feel Ready to Continue'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: AppBar(
        backgroundColor: AppColors.surface,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: AppColors.onSurface),
          onPressed: () => context.go(RoutePaths.home),
        ),
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: const BoxDecoration(
                color: AppColors.secondaryContainer,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.eco, size: 18, color: AppColors.primary),
            ),
            const SizedBox(width: 10),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Sanctuary Guide',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.onSurface),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    'Encrypted & confidential',
                    style: TextStyle(fontSize: 11, color: AppColors.secondary),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Restart chat',
            icon: const Icon(Icons.refresh, size: 20, color: AppColors.secondary),
            onPressed: () {
              AppStateService.instance.clearChat();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Chat restarted fresh.'),
                  duration: Duration(seconds: 1),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
          ),
          TextButton.icon(
            onPressed: () {
              AppStateService.instance.advanceAssessmentStep(2);
              context.go(RoutePaths.assessmentStatus);
            },
            icon: const Icon(Icons.check_circle_outline, size: 16, color: AppColors.primary),
            label: const Text(
              'Done',
              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.primary),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: Column(
              children: [
                // Top Reassurance Banner
                Container(
                  width: double.infinity,
                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLow,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.lock, size: 13, color: AppColors.secondary),
                      SizedBox(width: 6),
                      Flexible(
                        child: Text(
                          'Your words are safe. Take all the time you need.',
                          style: TextStyle(fontSize: 11.5, color: AppColors.secondary, fontWeight: FontWeight.w500),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),

                // Chat Messages List
                Expanded(
                  child: Builder(
                    builder: (context) {
                      final messages = AppStateService.instance.messages;
                      final hasDivider = messages.length > 2;
                      final totalCount = messages.length + (hasDivider ? 1 : 0);

                      return ListView.builder(
                        controller: _scrollController,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        itemCount: totalCount,
                        itemBuilder: (context, index) {
                          // Insert empathetic divider after the 2nd message if present
                          if (hasDivider && index == 2) {
                            return Padding(
                              padding: const EdgeInsets.symmetric(vertical: 12),
                              child: Center(
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: AppColors.surfaceContainerHigh,
                                    borderRadius: BorderRadius.circular(999),
                                  ),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.favorite, size: 14, color: AppColors.primary),
                                      SizedBox(width: 6),
                                      Flexible(
                                        child: Text(
                                          'Remember: You don\'t have to answer anything you aren\'t ready for.',
                                          style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500, color: AppColors.onSurfaceVariant),
                                          textAlign: TextAlign.center,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          }

                          final msgIndex = (hasDivider && index > 2) ? index - 1 : index;
                          final message = messages[msgIndex];

                      if (message.isAssistant) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                width: 28,
                                height: 28,
                                decoration: const BoxDecoration(
                                  color: AppColors.surfaceContainerHighest,
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(Icons.eco, size: 16, color: AppColors.primary),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(14),
                                      decoration: BoxDecoration(
                                        color: AppColors.surfaceContainerLowest,
                                        borderRadius: const BorderRadius.only(
                                          topRight: Radius.circular(16),
                                          bottomLeft: Radius.circular(16),
                                          bottomRight: Radius.circular(16),
                                          topLeft: Radius.circular(4),
                                        ),
                                        boxShadow: [
                                          BoxShadow(
                                            color: Colors.black.withValues(alpha: 0.02),
                                            blurRadius: 6,
                                            offset: const Offset(0, 2),
                                          ),
                                        ],
                                      ),
                                      child: Text(
                                        message.text,
                                        style: const TextStyle(
                                          fontSize: 14,
                                          height: 1.5,
                                          color: AppColors.onSurface,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'Sanctuary Guide • ${message.timestamp}',
                                      style: const TextStyle(fontSize: 11, color: AppColors.onSurfaceVariant),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        );
                      } else {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 14),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                              Flexible(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.all(14),
                                      decoration: const BoxDecoration(
                                        color: AppColors.secondaryContainer,
                                        borderRadius: BorderRadius.only(
                                          topLeft: Radius.circular(16),
                                          bottomLeft: Radius.circular(16),
                                          bottomRight: Radius.circular(16),
                                          topRight: Radius.circular(4),
                                        ),
                                      ),
                                      child: Text(
                                        message.text,
                                        style: const TextStyle(
                                          fontSize: 14,
                                          height: 1.5,
                                          color: AppColors.onSecondaryContainer,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(height: 4),
                                    const Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          'Shared by you',
                                          style: TextStyle(fontSize: 11, color: AppColors.onSurfaceVariant),
                                        ),
                                        SizedBox(width: 4),
                                        Icon(Icons.done_all, size: 14, color: AppColors.primary),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          );
                        }
                      },
                    );
                  },
                ),
              ),

                // Prompt Suggestion Chips
                SizedBox(
                  height: 38,
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    scrollDirection: Axis.horizontal,
                    itemCount: _promptSuggestions.length,
                    separatorBuilder: (context, index) => const SizedBox(width: 8),
                    itemBuilder: (context, index) {
                      final prompt = _promptSuggestions[index];
                      return ActionChip(
                        backgroundColor: AppColors.surfaceContainerLow,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                        label: Text(
                          prompt,
                          style: const TextStyle(fontSize: 12, color: AppColors.onSurface),
                        ),
                        onPressed: () => _sendMessage(prompt),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 10),

                // Interactive Input Card
                Container(
                  margin: const EdgeInsets.all(16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLowest,
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.04),
                        blurRadius: 10,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      TextField(
                        controller: _textController,
                        maxLines: 3,
                        minLines: 1,
                        decoration: InputDecoration(
                          hintText: _isListening
                              ? 'Listening gently... Take your time.'
                              : 'Type your thoughts here at your own pace...',
                          hintStyle: TextStyle(
                            fontSize: 13.5,
                            color: _isListening ? AppColors.primary : AppColors.onSurfaceVariant.withValues(alpha: 0.7),
                          ),
                          border: InputBorder.none,
                          fillColor: AppColors.surfaceContainerLow,
                          filled: true,
                          contentPadding: const EdgeInsets.all(12),
                          enabledBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: BorderSide.none,
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: AppColors.primary, width: 1.2),
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              // Mic dictation toggle
                              IconButton(
                                icon: Icon(
                                  _isListening ? Icons.mic : Icons.mic_none,
                                  color: _isListening ? AppColors.primary : AppColors.onSurfaceVariant,
                                  size: 20,
                                ),
                                onPressed: () {
                                  setState(() => _isListening = !_isListening);
                                },
                                tooltip: 'Dictate gently',
                              ),
                              // Grounding breathe button
                              InkWell(
                                onTap: _showBreathingModal,
                                borderRadius: BorderRadius.circular(999),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                                  decoration: BoxDecoration(
                                    color: AppColors.surfaceContainerLow,
                                    borderRadius: BorderRadius.circular(999),
                                  ),
                                  child: const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.self_improvement, size: 15, color: AppColors.primary),
                                      SizedBox(width: 4),
                                      Text(
                                        'Breathe',
                                        style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w500, color: AppColors.onSurfaceVariant),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                          // Send Button
                          FilledButton(
                            style: FilledButton.styleFrom(
                              backgroundColor: AppColors.primary,
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                              minimumSize: Size.zero,
                            ),
                            onPressed: () => _sendMessage(),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text('Send', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                                SizedBox(width: 4),
                                Icon(Icons.send, size: 14),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
