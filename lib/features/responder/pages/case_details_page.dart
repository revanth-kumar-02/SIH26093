import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';
import '../data/models/responder_models.dart';
import '../data/services/responder_api_service.dart';

/// Screen 14: Case Details
/// Comprehensive structured view incorporating AI Assessment evidence, deterministic SVI,
/// human recommendation decisioning, and immutable audit history.
class CaseDetailsPage extends StatefulWidget {
  final String caseId;

  const CaseDetailsPage({super.key, required this.caseId});

  @override
  State<CaseDetailsPage> createState() => _CaseDetailsPageState();
}

class _CaseDetailsPageState extends State<CaseDetailsPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoading = true;
  String? _error;
  CaseDetailModel? _case;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _fetchDetail();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final detail = await ResponderApiService.instance.fetchCaseDetail(widget.caseId);
      if (mounted) {
        setState(() {
          _case = detail;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString().replaceAll('ApiException: ', '');
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _handleDecision(String recId, String decision, {String? modifiedAction, String? note}) async {
    try {
      await ResponderApiService.instance.reviewRecommendation(
        widget.caseId,
        recId,
        decision,
        modifiedAction: modifiedAction,
        note: note,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Recommendation marked as $decision'),
          backgroundColor: decision == 'REJECT' ? AppColors.tertiary : AppColors.primary,
        ),
      );
      _fetchDetail();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error recording decision: $e'), backgroundColor: AppColors.tertiary),
      );
    }
  }

  void _showModifyDialog(RecommendationItemModel rec) {
    final actionController = TextEditingController(text: rec.responderAction);
    final noteController = TextEditingController();

    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Modify AI Recommendation'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Original AI Recommendation is preserved in audit records. Enter adjusted responder action:',
              style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: actionController,
              maxLines: 2,
              decoration: const InputDecoration(labelText: 'Modified Action', border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: noteController,
              maxLines: 2,
              decoration: const InputDecoration(labelText: 'Responder Observation / Note', border: OutlineInputBorder()),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Cancel')),
          FilledButton(
            onPressed: () {
              Navigator.of(ctx).pop();
              _handleDecision(
                rec.id,
                'MODIFY',
                modifiedAction: actionController.text.trim(),
                note: noteController.text.trim(),
              );
            },
            child: const Text('Save & Apply'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Text(_case != null ? 'Case: ${_case!.externalCaseReference}' : 'Case Details'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go(RoutePaths.responderCaseList),
        ),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchDetail),
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: Colors.white,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          tabs: const [
            Tab(icon: Icon(Icons.psychology_outlined), text: 'AI Assessment'),
            Tab(icon: Icon(Icons.analytics_outlined), text: 'SVI & Risk'),
            Tab(icon: Icon(Icons.recommend_outlined), text: 'Interventions'),
            Tab(icon: Icon(Icons.history_outlined), text: 'Audit History'),
          ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: AppColors.tertiary),
                      const SizedBox(height: 12),
                      Text(_error!, style: const TextStyle(color: AppColors.tertiary)),
                      const SizedBox(height: 16),
                      FilledButton(onPressed: _fetchDetail, child: const Text('Retry')),
                    ],
                  ),
                )
              : _case == null
                  ? const Center(child: Text('Case not found.'))
                  : Column(
                      children: [
                        if (_case!.immediateSafetyAttention || _case!.urgentHumanReview)
                          Container(
                            color: const Color(0xFFFDE8E4),
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                            child: const Row(
                              children: [
                                Icon(Icons.warning_amber_rounded, color: AppColors.tertiary, size: 20),
                                SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    'URGENT HUMAN REVIEW: Deterministic physical safety alert or critical risk threshold flagged.',
                                    style: TextStyle(
                                      color: AppColors.tertiary,
                                      fontWeight: FontWeight.w700,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        Expanded(
                          child: TabBarView(
                            controller: _tabController,
                            children: [
                              _buildAiAssessmentTab(),
                              _buildSviRiskTab(),
                              _buildInterventionsTab(),
                              _buildAuditTab(),
                            ],
                          ),
                        ),
                      ],
                    ),
    );
  }

  Widget _buildAiAssessmentTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 850),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                elevation: 1.5,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.auto_awesome, color: AppColors.primary, size: 20),
                          SizedBox(width: 8),
                          Text('Gemma 3n E2B IT Multimodal Assessment', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                        ],
                      ),
                      const Divider(height: 20),
                      Text(
                        _case!.aiSummary ?? 'Structured assessment evidence generated from complainant voice & text signals.',
                        style: const TextStyle(fontSize: 14, height: 1.5),
                      ),
                      const SizedBox(height: 14),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.background,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.black12),
                        ),
                        child: const Row(
                          children: [
                            Icon(Icons.info_outline, size: 16, color: AppColors.onSurfaceVariant),
                            SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                'AI-assisted vulnerability/risk triage indicator. Not a clinical diagnosis or definitive legal finding.',
                                style: TextStyle(fontSize: 11, color: AppColors.onSurfaceVariant, fontStyle: FontStyle.italic),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                elevation: 1.5,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Complainant Interaction Log', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                          Text(
                            '${_case!.messages.length} Messages',
                            style: const TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant),
                          ),
                        ],
                      ),
                      const Divider(height: 20),
                      if (_case!.messages.isEmpty)
                        const Text('No intake messages recorded in session.', style: TextStyle(color: AppColors.onSurfaceVariant))
                      else
                        ..._case!.messages.map((m) {
                          final isVictim = m['sender_type'] == 'VICTIM';
                          final isVoice = m['input_source'] == 'VOICE';

                          return Container(
                            margin: const EdgeInsets.only(bottom: 10),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: isVictim ? AppColors.surfaceContainerLowest : const Color(0xFFF1F4EE),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: isVictim ? AppColors.primary.withValues(alpha: 0.2) : Colors.black12),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Icon(
                                      isVictim ? Icons.person : Icons.smart_toy_outlined,
                                      size: 14,
                                      color: isVictim ? AppColors.primary : AppColors.onSurfaceVariant,
                                    ),
                                    const SizedBox(width: 6),
                                    Text(
                                      isVictim ? 'Complainant' : 'TrueVoice Assistant',
                                      style: TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w700,
                                        color: isVictim ? AppColors.primary : AppColors.onSurfaceVariant,
                                      ),
                                    ),
                                    if (isVoice) ...[
                                      const SizedBox(width: 8),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                        decoration: BoxDecoration(
                                          color: Colors.purple.shade50,
                                          borderRadius: BorderRadius.circular(4),
                                          border: Border.all(color: Colors.purple.shade200),
                                        ),
                                        child: const Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Icon(Icons.mic, size: 10, color: Colors.purple),
                                            SizedBox(width: 2),
                                            Text('VOICE ASR', style: TextStyle(fontSize: 9, color: Colors.purple, fontWeight: FontWeight.bold)),
                                          ],
                                        ),
                                      ),
                                    ],
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  m['content']?.toString() ?? '',
                                  style: const TextStyle(fontSize: 13, height: 1.4),
                                ),
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSviRiskTab() {
    final score = _case!.sviScore ?? 0.0;
    final category = _case!.riskCategory ?? 'PENDING';
    final contributions = _case!.factorContributions;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 850),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Row(
                    children: [
                      Container(
                        width: 90,
                        height: 90,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: _getRiskColor(category).withValues(alpha: 0.12),
                          border: Border.all(color: _getRiskColor(category), width: 3),
                        ),
                        alignment: Alignment.center,
                        child: Text(
                          score.toStringAsFixed(1),
                          style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: _getRiskColor(category)),
                        ),
                      ),
                      const SizedBox(width: 24),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '$category RISK TRIAGE',
                              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: _getRiskColor(category)),
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              'Deterministic Stress Vulnerability Index (SVI v1.0)',
                              style: TextStyle(fontSize: 13, color: AppColors.onSurfaceVariant),
                            ),
                            const SizedBox(height: 8),
                            LinearProgressIndicator(
                              value: (score / 100.0).clamp(0.0, 1.0),
                              backgroundColor: Colors.grey.shade200,
                              color: _getRiskColor(category),
                              minHeight: 8,
                              borderRadius: BorderRadius.circular(4),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                elevation: 1.5,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Vulnerability Factor Contributions', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      const SizedBox(height: 12),
                      if (contributions.isEmpty)
                        const Text('No individual factor weights recorded.', style: TextStyle(color: AppColors.onSurfaceVariant))
                      else
                        ...contributions.entries.map((e) {
                          final val = (e.value as num?)?.toDouble() ?? 0.0;
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(
                                      e.key.replaceAll('_', ' ').toUpperCase(),
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                                    ),
                                    Text(
                                      '+${val.toStringAsFixed(1)} pts',
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                LinearProgressIndicator(
                                  value: (val / 35.0).clamp(0.0, 1.0),
                                  backgroundColor: Colors.grey.shade100,
                                  color: AppColors.primary,
                                  minHeight: 5,
                                  borderRadius: BorderRadius.circular(3),
                                ),
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                elevation: 1.5,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                color: Colors.white,
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Key Drivers & Uncertainties', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                      const SizedBox(height: 10),
                      const Text('Key Drivers:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      const SizedBox(height: 6),
                      if (_case!.keyDrivers.isEmpty)
                        const Text('None detected.', style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant))
                      else
                        ..._case!.keyDrivers.map((d) => Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Row(
                                children: [
                                  const Icon(Icons.check_circle_outline, size: 14, color: AppColors.primary),
                                  const SizedBox(width: 8),
                                  Text(d, style: const TextStyle(fontSize: 13)),
                                ],
                              ),
                            )),
                      const SizedBox(height: 12),
                      const Text('Uncertainties / Limitations:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                      const SizedBox(height: 6),
                      if (_case!.uncertainties.isEmpty)
                        const Text('No conflicting signals noted.', style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant))
                      else
                        ..._case!.uncertainties.map((u) => Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Row(
                                children: [
                                  const Icon(Icons.help_outline, size: 14, color: Colors.orange),
                                  const SizedBox(width: 8),
                                  Expanded(child: Text(u, style: const TextStyle(fontSize: 13, color: AppColors.onSurfaceVariant))),
                                ],
                              ),
                            )),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInterventionsTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 850),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'AI-Suggested Support Pathways & Human Review Decisioning',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              const SizedBox(height: 6),
              const Text(
                'The human responder retains final operational authority over every pathway.',
                style: TextStyle(fontSize: 13, color: AppColors.onSurfaceVariant),
              ),
              const SizedBox(height: 16),
              if (_case!.recommendations.isEmpty)
                Container(
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14)),
                  child: const Center(child: Text('No recommendations generated for this case.')),
                )
              else
                ..._case!.recommendations.map((rec) => _buildRecommendationCard(rec)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRecommendationCard(RecommendationItemModel rec) {
    final isReviewed = rec.status != 'PENDING';

    return Card(
      elevation: 2,
      margin: const EdgeInsets.only(bottom: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: _getPriorityColor(rec.priority).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: _getPriorityColor(rec.priority)),
                  ),
                  child: Text(
                    rec.priority,
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: _getPriorityColor(rec.priority)),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isReviewed ? AppColors.primary.withValues(alpha: 0.12) : Colors.grey.shade100,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    rec.status,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: isReviewed ? AppColors.primary : AppColors.onSurfaceVariant,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(rec.category.replaceAll('_', ' '), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(height: 6),
            Text(rec.responderAction, style: const TextStyle(fontSize: 14, height: 1.4)),
            const SizedBox(height: 10),
            Text(
              'Evidence & Reason: ${rec.reason}',
              style: const TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant, fontStyle: FontStyle.italic),
            ),
            const Divider(height: 24),
            if (isReviewed) ...[
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F4EE),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle, size: 16, color: AppColors.primary),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Reviewed by ${rec.reviewedBy ?? "Responder"}: ${rec.status} ${rec.responderNote != null ? "• Note: ${rec.responderNote}" : ""}',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
            ] else ...[
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  OutlinedButton(
                    style: OutlinedButton.styleFrom(foregroundColor: AppColors.tertiary),
                    onPressed: () => _handleDecision(rec.id, 'REJECT'),
                    child: const Text('Reject'),
                  ),
                  const SizedBox(width: 8),
                  OutlinedButton(
                    onPressed: () => _showModifyDialog(rec),
                    child: const Text('Modify'),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    style: FilledButton.styleFrom(backgroundColor: AppColors.primary),
                    onPressed: () => _handleDecision(rec.id, 'ACCEPT'),
                    child: const Text('Accept'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAuditTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 850),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Row(
                children: [
                  Icon(Icons.lock_clock, color: AppColors.primary, size: 20),
                  SizedBox(width: 8),
                  Text('Append-Only Audit Log', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ],
              ),
              const SizedBox(height: 4),
              const Text(
                'Verifiable log of case views, assignments, and human reviews.',
                style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant),
              ),
              const SizedBox(height: 16),
              if (_case!.auditHistory.isEmpty)
                const Text('No audit events recorded.')
              else
                ..._case!.auditHistory.map((a) => Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.black12),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(Icons.history, size: 18, color: AppColors.primary),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    Text(a.eventType, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                    Text(
                                      '${a.createdAt.hour}:${a.createdAt.minute.toString().padLeft(2, '0')}',
                                      style: const TextStyle(fontSize: 11, color: AppColors.onSurfaceVariant),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                Text('Actor: ${a.actorType} (${a.actorId})', style: const TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant)),
                                if (a.metadata.isNotEmpty) ...[
                                  const SizedBox(height: 4),
                                  Text(
                                    a.metadata.toString(),
                                    style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic, color: Colors.black54),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ],
                      ),
                    )),
            ],
          ),
        ),
      ),
    );
  }

  Color _getRiskColor(String category) {
    switch (category.toUpperCase()) {
      case 'CRITICAL':
        return AppColors.tertiary;
      case 'HIGH':
        return Colors.amber.shade900;
      case 'MODERATE':
        return Colors.blue.shade700;
      case 'LOW':
        return AppColors.primary;
      default:
        return Colors.grey;
    }
  }

  Color _getPriorityColor(String priority) {
    switch (priority.toUpperCase()) {
      case 'IMMEDIATE_ESCALATION':
        return AppColors.tertiary;
      case 'URGENT':
        return Colors.deepOrange;
      case 'HIGH_PRIORITY':
        return Colors.amber.shade900;
      case 'STANDARD':
        return Colors.blue.shade700;
      default:
        return AppColors.primary;
    }
  }
}
