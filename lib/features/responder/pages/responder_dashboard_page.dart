import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';
import '../data/models/responder_models.dart';
import '../data/services/responder_api_service.dart';

/// Screen 12: Responder Dashboard
/// Central operational hub featuring urgent triage queue, risk distribution metrics, and workflow navigation.
class ResponderDashboardPage extends StatefulWidget {
  const ResponderDashboardPage({super.key});

  @override
  State<ResponderDashboardPage> createState() => _ResponderDashboardPageState();
}

class _ResponderDashboardPageState extends State<ResponderDashboardPage> {
  bool _isLoading = true;
  List<CaseListItemModel> _cases = [];

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final cases = await ResponderApiService.instance.fetchCases(pageSize: 50);
      if (mounted) {
        setState(() {
          _cases = cases;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _handleLogout() {
    ResponderApiService.instance.logout();
    context.go(RoutePaths.responderLogin);
  }

  @override
  Widget build(BuildContext context) {
    final session = ResponderApiService.instance.session;
    final urgentCases = _cases.where((c) => c.immediateSafetyAttention || c.urgentHumanReview).toList();
    final criticalCount = _cases.where((c) => c.latestRiskCategory?.toUpperCase() == 'CRITICAL').length;
    final highCount = _cases.where((c) => c.latestRiskCategory?.toUpperCase() == 'HIGH').length;
    final inReviewCount = _cases.where((c) => c.status == 'IN_REVIEW' || c.status == 'AWAITING_RESPONDER_ACTION').length;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('NHAA 14566 — Operational Triage Dashboard'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh queue',
            onPressed: _loadDashboardData,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: _handleLogout,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadDashboardData,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 1000),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        // Responder Greeting & Role Card
                        Card(
                          elevation: 2,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          color: Colors.white,
                          child: Padding(
                            padding: const EdgeInsets.all(20),
                            child: Row(
                              children: [
                                CircleAvatar(
                                  radius: 26,
                                  backgroundColor: AppColors.primary.withValues(alpha: 0.15),
                                  child: const Icon(Icons.person, color: AppColors.primary, size: 28),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        session?.displayName ?? 'Duty Responder',
                                        style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
                                      ),
                                      const SizedBox(height: 4),
                                      Wrap(
                                        spacing: 8,
                                        runSpacing: 4,
                                        crossAxisAlignment: WrapCrossAlignment.center,
                                        children: [
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                            decoration: BoxDecoration(
                                              color: AppColors.primary.withValues(alpha: 0.12),
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              session?.role ?? 'ADMIN',
                                              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.primary),
                                            ),
                                          ),
                                          const Text(
                                            'Duty Station Active • Real-time Triage Hub',
                                            style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                                OutlinedButton.icon(
                                  onPressed: () => context.go(RoutePaths.responderCaseList),
                                  icon: const Icon(Icons.list_alt, size: 18),
                                  label: const Text('View All Cases'),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),

                        // Urgent Safety Queue Banner (if any)
                        if (urgentCases.isNotEmpty) ...[
                          Container(
                            padding: const EdgeInsets.all(18),
                            decoration: BoxDecoration(
                              color: const Color(0xFFFDE8E4),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: AppColors.tertiary, width: 1.5),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    const Icon(Icons.warning_amber_rounded, color: AppColors.tertiary, size: 24),
                                    const SizedBox(width: 10),
                                    Text(
                                      'URGENT HUMAN REVIEW QUEUE (${urgentCases.length} CASE${urgentCases.length > 1 ? "S" : ""})',
                                      style: const TextStyle(
                                        color: AppColors.tertiary,
                                        fontWeight: FontWeight.w800,
                                        fontSize: 14,
                                        letterSpacing: 0.5,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  'Deterministic physical safety or critical threshold triggered. Immediate human review required:',
                                  style: TextStyle(fontSize: 13, color: AppColors.onSurfaceVariant),
                                ),
                                const SizedBox(height: 12),
                                ...urgentCases.map((c) => Container(
                                      margin: const EdgeInsets.only(bottom: 8),
                                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                      decoration: BoxDecoration(
                                        color: Colors.white,
                                        borderRadius: BorderRadius.circular(10),
                                        border: Border.all(color: AppColors.tertiary.withValues(alpha: 0.4)),
                                      ),
                                      child: Row(
                                        children: [
                                          const Icon(Icons.priority_high, color: AppColors.tertiary, size: 18),
                                          const SizedBox(width: 8),
                                          Text(
                                            c.externalCaseReference,
                                            style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                                          ),
                                          const SizedBox(width: 12),
                                          Container(
                                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                            decoration: BoxDecoration(
                                              color: AppColors.tertiary,
                                              borderRadius: BorderRadius.circular(6),
                                            ),
                                            child: Text(
                                              'SVI ${(c.latestSviScore ?? 0).toStringAsFixed(1)} • ${c.latestRiskCategory ?? "CRITICAL"}',
                                              style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                                            ),
                                          ),
                                          const Spacer(),
                                          FilledButton.tonal(
                                            style: FilledButton.styleFrom(
                                              backgroundColor: AppColors.tertiary.withValues(alpha: 0.12),
                                              foregroundColor: AppColors.tertiary,
                                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                                            ),
                                            onPressed: () => context.go('/responder/cases/${c.id}'),
                                            child: const Text('Open Triage', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                          ),
                                        ],
                                      ),
                                    )),
                              ],
                            ),
                          ),
                          const SizedBox(height: 20),
                        ],

                        // Metrics Grid
                        LayoutBuilder(
                          builder: (context, constraints) {
                            final itemWidth = constraints.maxWidth > 650
                                ? (constraints.maxWidth - 36) / 4
                                : (constraints.maxWidth - 12) / 2;
                            return Wrap(
                              spacing: 12,
                              runSpacing: 12,
                              children: [
                                SizedBox(
                                  width: itemWidth,
                                  child: _buildMetricCard(
                                    title: 'Total Cases',
                                    value: '${_cases.length}',
                                    icon: Icons.folder_shared_outlined,
                                    color: AppColors.primary,
                                  ),
                                ),
                                SizedBox(
                                  width: itemWidth,
                                  child: _buildMetricCard(
                                    title: 'Critical Risk',
                                    value: '$criticalCount',
                                    icon: Icons.report_problem_outlined,
                                    color: AppColors.tertiary,
                                  ),
                                ),
                                SizedBox(
                                  width: itemWidth,
                                  child: _buildMetricCard(
                                    title: 'High Risk',
                                    value: '$highCount',
                                    icon: Icons.warning_amber_outlined,
                                    color: Colors.amber.shade800,
                                  ),
                                ),
                                SizedBox(
                                  width: itemWidth,
                                  child: _buildMetricCard(
                                    title: 'Active Review',
                                    value: '$inReviewCount',
                                    icon: Icons.pending_actions_outlined,
                                    color: Colors.blue.shade700,
                                  ),
                                ),
                              ],
                            );
                          },
                        ),
                        const SizedBox(height: 24),

                        // Section Title: Recent Cases
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Recent Intake & Assessment Feed',
                              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                            ),
                            TextButton.icon(
                              onPressed: () => context.go(RoutePaths.responderCaseList),
                              icon: const Icon(Icons.arrow_forward, size: 16),
                              label: const Text('All Cases'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),

                        if (_cases.isEmpty)
                          Container(
                            padding: const EdgeInsets.all(32),
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: const Text('No cases in queue.', style: TextStyle(color: AppColors.onSurfaceVariant)),
                          )
                        else
                          ..._cases.take(5).map((c) => _buildCaseTile(c)),
                      ],
                    ),
                  ),
                ),
              ),
            ),
    );
  }

  Widget _buildMetricCard({
    required String title,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Card(
      elevation: 1.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 12),
            Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: color)),
            const SizedBox(height: 4),
            Text(title, style: const TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }

  Widget _buildCaseTile(CaseListItemModel c) {
    final riskColor = _getRiskColor(c.latestRiskCategory);

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      color: Colors.white,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          width: 44,
          height: 44,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: riskColor.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            c.latestSviScore != null ? c.latestSviScore!.toInt().toString() : '—',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: riskColor),
          ),
        ),
        title: Row(
          children: [
            Text(c.externalCaseReference, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14)),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: riskColor.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                c.latestRiskCategory ?? 'PENDING',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: riskColor),
              ),
            ),
          ],
        ),
        subtitle: Text(
          'Status: ${c.status} • Lang: ${c.language.toUpperCase()} • Assigned: ${c.assignedResponderName ?? "Unassigned"}',
          style: const TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant),
        ),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.go('/responder/cases/${c.id}'),
      ),
    );
  }

  Color _getRiskColor(String? category) {
    switch (category?.toUpperCase()) {
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
}
