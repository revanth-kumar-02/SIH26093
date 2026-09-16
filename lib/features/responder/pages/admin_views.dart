import '../../../core/network/api_exceptions.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/routes/route_paths.dart';
import '../../../core/theme/app_colors.dart';
import '../data/models/responder_models.dart';
import '../data/services/responder_api_service.dart';
import 'admin_shell_layout.dart';

// =============================================================================
// 1. ADMIN OVERVIEW / DASHBOARD PAGE
// =============================================================================

class AdminDashboardPage extends StatefulWidget {
  const AdminDashboardPage({super.key});

  @override
  State<AdminDashboardPage> createState() => _AdminDashboardPageState();
}

class _AdminDashboardPageState extends State<AdminDashboardPage> {
  DashboardAnalyticsModel? _analytics;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final data = await ResponderApiService.instance.fetchAdminDashboard();
      if (mounted) {
        setState(() {
          _analytics = data;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e is ApiException ? e.userMessage : 'Unable to load dashboard data. Please try again.';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminShellLayout(
      currentPath: RoutePaths.adminDashboard,
      title: 'Overview',
      breadcrumb: 'Admin / Overview',
      onRefresh: _loadDashboardData,
      child: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(strokeWidth: 2.5),
            SizedBox(height: 16),
            Text('Loading cases...'),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Container(
          padding: const EdgeInsets.all(24),
          constraints: const BoxConstraints(maxWidth: 420),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48, color: AppColors.error),
              const SizedBox(height: 12),
              Text(
                'Unable to load cases.',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(_errorMessage!, textAlign: TextAlign.center, style: const TextStyle(fontSize: 13)),
              const SizedBox(height: 20),
              FilledButton.tonal(
                onPressed: _loadDashboardData,
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      );
    }

    final a = _analytics!;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Subtitle
          Text(
            'Monitor cases requiring human review and support.',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.onSurfaceVariant,
                ),
          ),
          const SizedBox(height: 20),

          // 4 Compact Summary Cards
          Row(
            children: [
              Expanded(
                child: _buildSummaryCard(
                  title: 'Active Cases',
                  value: a.activeCases.toString(),
                  contextText: 'Open in system',
                  icon: Icons.folder_open,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: _buildSummaryCard(
                  title: 'Urgent Review',
                  value: a.urgentReview.toString(),
                  contextText: 'Immediate safety or review',
                  icon: Icons.warning_amber_rounded,
                  color: AppColors.tertiary,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: _buildSummaryCard(
                  title: 'High Risk',
                  value: a.highRisk.toString(),
                  contextText: 'High or Critical SVI',
                  icon: Icons.priority_high_rounded,
                  color: AppColors.statusModerate,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: _buildSummaryCard(
                  title: 'Pending Reviews',
                  value: a.pendingReviews.toString(),
                  contextText: 'Awaiting human decision',
                  icon: Icons.assignment_late_outlined,
                  color: AppColors.secondary,
                ),
              ),
            ],
          ),

          const SizedBox(height: 28),

          // Risk Overview Distribution Component
          _buildRiskDistributionSection(a.riskDistribution),

          const SizedBox(height: 28),

          // Urgent Review Section ("Requires Attention")
          _buildRequiresAttentionSection(a.requiresAttentionCases),

          const SizedBox(height: 28),

          // Recent Cases Table
          _buildRecentCasesTable(a.recentCases),
        ],
      ),
    );
  }

  Widget _buildSummaryCard({
    required String title,
    required String value,
    required String contextText,
    required IconData icon,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.surfaceMutedText,
                ),
              ),
              Icon(icon, size: 18, color: color),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontSize: 26,
              fontWeight: FontWeight.w700,
              color: AppColors.onSurface,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            contextText,
            style: const TextStyle(fontSize: 11, color: AppColors.surfaceMutedText),
          ),
        ],
      ),
    );
  }

  Widget _buildRiskDistributionSection(Map<String, int> dist) {
    final total = dist.values.fold<int>(0, (prev, e) => prev + e);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Risk Distribution (Operational Visibility)',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.onSurface),
              ),
              Text(
                '$total Active Cases Categorized',
                style: const TextStyle(fontSize: 12, color: AppColors.surfaceMutedText),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              _buildRiskBadge('LOW', dist['LOW'] ?? 0, total, AppColors.statusLow),
              const SizedBox(width: 12),
              _buildRiskBadge('MODERATE', dist['MODERATE'] ?? 0, total, AppColors.statusModerate),
              const SizedBox(width: 12),
              _buildRiskBadge('HIGH', dist['HIGH'] ?? 0, total, AppColors.statusHigh),
              const SizedBox(width: 12),
              _buildRiskBadge('CRITICAL', dist['CRITICAL'] ?? 0, total, AppColors.statusCritical),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRiskBadge(String category, int count, int total, Color color) {
    final pct = total > 0 ? ((count / total) * 100).toStringAsFixed(0) : '0';
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.08),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withValues(alpha: 0.25)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  category,
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color),
                ),
                Text('$pct%', style: TextStyle(fontSize: 10, color: color)),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '$count cases',
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppColors.onSurface),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRequiresAttentionSection(List<CaseListItemModel> cases) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.3))),
            ),
            child: Row(
              children: [
                const Icon(Icons.emergency_outlined, size: 18, color: AppColors.tertiary),
                const SizedBox(width: 8),
                const Text(
                  'Requires Attention',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.onSurface),
                ),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.tertiary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${cases.length} cases',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.tertiary),
                  ),
                ),
              ],
            ),
          ),
          if (cases.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(
                child: Text('No urgent cases requiring immediate attention.', style: TextStyle(color: AppColors.surfaceMutedText)),
              ),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: cases.length,
              separatorBuilder: (_, _) => Divider(height: 1, color: AppColors.outlineVariant.withValues(alpha: 0.2)),
              itemBuilder: (context, index) {
                final c = cases[index];
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  child: Row(
                    children: [
                      Expanded(
                        flex: 2,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              c.externalCaseReference,
                              style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                            ),
                            Text(
                              'Language: ${c.language.toUpperCase()}',
                              style: const TextStyle(fontSize: 11, color: AppColors.surfaceMutedText),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        flex: 2,
                        child: Row(
                          children: [
                            _buildRiskChip(c.latestRiskCategory ?? 'LOW'),
                            if (c.immediateSafetyAttention) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: AppColors.tertiary.withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: const Text(
                                  'SAFETY FLAG',
                                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppColors.tertiary),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                      Expanded(
                        flex: 2,
                        child: Text(
                          c.status,
                          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                        ),
                      ),
                      OutlinedButton(
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.primary,
                          side: const BorderSide(color: AppColors.primary),
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          visualDensity: VisualDensity.compact,
                        ),
                        onPressed: () => context.go('/admin/cases/${c.id}'),
                        child: const Text('Review Case'),
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildRecentCasesTable(List<CaseListItemModel> cases) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: BoxDecoration(
              border: Border(bottom: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.3))),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Recent Cases',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.onSurface),
                ),
                TextButton(
                  onPressed: () => context.go(RoutePaths.adminCases),
                  child: const Text('View All Cases', style: TextStyle(fontSize: 12, color: AppColors.primary)),
                ),
              ],
            ),
          ),
          if (cases.isEmpty)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: Text('No cases found.', style: TextStyle(color: AppColors.surfaceMutedText))),
            )
          else
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                headingRowHeight: 40,
                dataRowMinHeight: 48,
                dataRowMaxHeight: 52,
                columns: const [
                  DataColumn(label: Text('Case ID', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Language', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Risk', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Status', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Last Updated', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                  DataColumn(label: Text('Action', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold))),
                ],
                rows: cases.map((c) {
                  return DataRow(
                    cells: [
                      DataCell(Text(c.externalCaseReference, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13))),
                      DataCell(Text(c.language.toUpperCase(), style: const TextStyle(fontSize: 12))),
                      DataCell(_buildRiskChip(c.latestRiskCategory ?? 'LOW')),
                      DataCell(Text(c.status, style: const TextStyle(fontSize: 12))),
                      DataCell(Text(
                        '${c.updatedAt.hour.toString().padLeft(2, '0')}:${c.updatedAt.minute.toString().padLeft(2, '0')}',
                        style: const TextStyle(fontSize: 12, color: AppColors.surfaceMutedText),
                      )),
                      DataCell(
                        InkWell(
                          onTap: () => context.go('/admin/cases/${c.id}'),
                          child: const Padding(
                            padding: EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                            child: Text('View', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ),
                    ],
                  );
                }).toList(),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildRiskChip(String risk) {
    Color bg;
    Color fg;
    switch (risk.toUpperCase()) {
      case 'CRITICAL':
        bg = AppColors.statusCritical.withValues(alpha: 0.12);
        fg = AppColors.statusCritical;
        break;
      case 'HIGH':
        bg = AppColors.statusHigh.withValues(alpha: 0.12);
        fg = AppColors.statusHigh;
        break;
      case 'MODERATE':
        bg = AppColors.statusModerate.withValues(alpha: 0.12);
        fg = AppColors.statusModerate;
        break;
      default:
        bg = AppColors.statusLow.withValues(alpha: 0.12);
        fg = AppColors.statusLow;
    }
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        risk.toUpperCase(),
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: fg),
      ),
    );
  }
}

// =============================================================================
// 2. ADMIN CASES LIST PAGE
// =============================================================================

class AdminCasesPage extends StatefulWidget {
  const AdminCasesPage({super.key});

  @override
  State<AdminCasesPage> createState() => _AdminCasesPageState();
}

class _AdminCasesPageState extends State<AdminCasesPage> {
  List<CaseListItemModel> _cases = [];
  bool _isLoading = true;
  String? _errorMessage;

  String _searchQuery = '';
  String _selectedRisk = 'ALL';
  String _selectedStatus = 'ALL';

  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _fetchCases();
  }

  Future<void> _fetchCases() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final items = await ResponderApiService.instance.fetchAdminCases(
        status: _selectedStatus == 'ALL' ? null : _selectedStatus,
        riskCategory: _selectedRisk == 'ALL' ? null : _selectedRisk,
        search: _searchQuery.isEmpty ? null : _searchQuery,
      );
      if (mounted) {
        setState(() {
          _cases = items;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e is ApiException ? e.userMessage : 'Failed to retrieve cases.';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminShellLayout(
      currentPath: RoutePaths.adminCases,
      title: 'Case Management',
      breadcrumb: 'Admin / Cases',
      onRefresh: _fetchCases,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Filter Bar
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainerLowest,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
              ),
              child: Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: TextField(
                      controller: _searchController,
                      decoration: InputDecoration(
                        hintText: 'Search by Case Reference (e.g. NHAA-2026)...',
                        prefixIcon: const Icon(Icons.search, size: 20),
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onSubmitted: (val) {
                        _searchQuery = val.trim();
                        _fetchCases();
                      },
                    ),
                  ),
                  const SizedBox(width: 14),
                  // Risk filter
                  DropdownButton<String>(
                    value: _selectedRisk,
                    underline: const SizedBox(),
                    items: const [
                      DropdownMenuItem(value: 'ALL', child: Text('Risk: All')),
                      DropdownMenuItem(value: 'LOW', child: Text('Low')),
                      DropdownMenuItem(value: 'MODERATE', child: Text('Moderate')),
                      DropdownMenuItem(value: 'HIGH', child: Text('High')),
                      DropdownMenuItem(value: 'CRITICAL', child: Text('Critical')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _selectedRisk = val);
                        _fetchCases();
                      }
                    },
                  ),
                  const SizedBox(width: 14),
                  // Status filter
                  DropdownButton<String>(
                    value: _selectedStatus,
                    underline: const SizedBox(),
                    items: const [
                      DropdownMenuItem(value: 'ALL', child: Text('Status: All')),
                      DropdownMenuItem(value: 'NEW', child: Text('New')),
                      DropdownMenuItem(value: 'IN_REVIEW', child: Text('In Review')),
                      DropdownMenuItem(value: 'AWAITING_RESPONDER_ACTION', child: Text('Awaiting Action')),
                      DropdownMenuItem(value: 'ACTION_RECORDED', child: Text('Action Recorded')),
                      DropdownMenuItem(value: 'CLOSED', child: Text('Closed')),
                    ],
                    onChanged: (val) {
                      if (val != null) {
                        setState(() => _selectedStatus = val);
                        _fetchCases();
                      }
                    },
                  ),
                  const SizedBox(width: 12),
                  FilledButton.tonal(
                    onPressed: () {
                      _searchQuery = _searchController.text.trim();
                      _fetchCases();
                    },
                    child: const Text('Filter'),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 18),

            // Case Table Area
            Expanded(
              child: _buildCaseList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCaseList() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_errorMessage!, style: const TextStyle(color: AppColors.error)),
            const SizedBox(height: 12),
            FilledButton.tonal(onPressed: _fetchCases, child: const Text('Retry')),
          ],
        ),
      );
    }

    if (_cases.isEmpty) {
      return Center(
        child: Container(
          padding: const EdgeInsets.all(24),
          child: const Text('No cases found matching the criteria.', style: TextStyle(color: AppColors.surfaceMutedText)),
        ),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: ListView.separated(
        itemCount: _cases.length,
        separatorBuilder: (_, _) => Divider(height: 1, color: AppColors.outlineVariant.withValues(alpha: 0.2)),
        itemBuilder: (context, index) {
          final c = _cases[index];
          return ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
            title: Row(
              children: [
                Text(
                  c.externalCaseReference,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.primarySage.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    c.language.toUpperCase(),
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ),
                const SizedBox(width: 8),
                if (c.immediateSafetyAttention)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.tertiary.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'SAFETY ALERT',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.tertiary),
                    ),
                  ),
              ],
            ),
            subtitle: Text('Status: ${c.status}  •  Updated: ${c.updatedAt.toLocal().toString().substring(0, 16)}'),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (c.latestSviScore != null) ...[
                  Text(
                    'SVI: ${c.latestSviScore!.toStringAsFixed(0)}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  const SizedBox(width: 10),
                ],
                OutlinedButton(
                  onPressed: () => context.go('/admin/cases/${c.id}'),
                  child: const Text('Review'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

// =============================================================================
// 3. ADMIN CASE DETAIL PAGE
// =============================================================================

class AdminCaseDetailPage extends StatefulWidget {
  final String caseId;

  const AdminCaseDetailPage({super.key, required this.caseId});

  @override
  State<AdminCaseDetailPage> createState() => _AdminCaseDetailPageState();
}

class _AdminCaseDetailPageState extends State<AdminCaseDetailPage> {
  CaseDetailModel? _detail;
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadCase();
  }

  Future<void> _loadCase() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final res = await ResponderApiService.instance.fetchAdminCaseDetail(widget.caseId);
      if (mounted) {
        setState(() {
          _detail = res;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e is ApiException ? e.userMessage : 'Failed to retrieve case details.';
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _handleDecision(String recId, String decision) async {
    if (decision == 'MODIFY') {
      _showModifyDialog(recId);
      return;
    }

    try {
      await ResponderApiService.instance.adminReviewRecommendation(recId, decision);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Recommendation marked as $decision.')),
      );
      _loadCase();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    }
  }

  void _showModifyDialog(String recId) {
    final actionController = TextEditingController();
    final noteController = TextEditingController();
    String selectedPriority = 'STANDARD';

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Modify AI Recommendation'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Priority:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
            const SizedBox(height: 6),
            DropdownButton<String>(
              value: selectedPriority,
              isExpanded: true,
              items: const [
                DropdownMenuItem(value: 'STANDARD', child: Text('Standard')),
                DropdownMenuItem(value: 'HIGH_PRIORITY', child: Text('High Priority')),
                DropdownMenuItem(value: 'CRITICAL', child: Text('Critical Priority')),
              ],
              onChanged: (v) => selectedPriority = v ?? 'STANDARD',
            ),
            const SizedBox(height: 12),
            const Text('Updated Responder Action:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
            const SizedBox(height: 6),
            TextField(
              controller: actionController,
              decoration: const InputDecoration(
                hintText: 'Enter modified action plan...',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
            ),
            const SizedBox(height: 12),
            const Text('Admin Note / Justification:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
            const SizedBox(height: 6),
            TextField(
              controller: noteController,
              decoration: const InputDecoration(
                hintText: 'Reason for adjustment...',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              Navigator.pop(ctx);
              try {
                await ResponderApiService.instance.adminReviewRecommendation(
                  recId,
                  'MODIFY',
                  modifiedAction: actionController.text.trim(),
                  modifiedPriority: selectedPriority,
                  note: noteController.text.trim(),
                );
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Recommendation modified and logged.')),
                );
                _loadCase();
              } catch (e) {
                if (!mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Error: ${e.toString()}')),
                );
              }
            },
            child: const Text('Save Modification'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AdminShellLayout(
      currentPath: RoutePaths.adminCases,
      title: _detail?.externalCaseReference ?? 'Case Details',
      breadcrumb: 'Admin / Cases / ${_detail?.externalCaseReference ?? widget.caseId}',
      onRefresh: _loadCase,
      child: _buildContent(),
    );
  }

  Widget _buildContent() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_errorMessage!, style: const TextStyle(color: AppColors.error)),
            const SizedBox(height: 12),
            FilledButton.tonal(onPressed: _loadCase, child: const Text('Retry')),
          ],
        ),
      );
    }

    final d = _detail!;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Card
          _buildHeaderCard(d),
          const SizedBox(height: 20),

          // SVI Presentation Card (Non-Diagnostic)
          _buildSviCard(d),
          const SizedBox(height: 20),

          // Structured AI Assessment
          _buildAssessmentCard(d),
          const SizedBox(height: 20),

          // Conversation Transcript
          _buildConversationCard(d),
          const SizedBox(height: 20),

          // Support Recommendations & Human Review
          _buildRecommendationsCard(d),
          const SizedBox(height: 20),

          // Audit History
          _buildAuditHistoryCard(d),
        ],
      ),
    );
  }

  Widget _buildHeaderCard(CaseDetailModel d) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      d.externalCaseReference,
                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(width: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        d.status,
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.primary),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Language: ${d.language.toUpperCase()}  •  Consent: ${d.consentStatus}  •  Created: ${d.createdAt.toLocal().toString().substring(0, 16)}'),
              ],
            ),
          ),
          OutlinedButton.icon(
            icon: const Icon(Icons.arrow_back, size: 16),
            label: const Text('Back to Cases'),
            onPressed: () => context.go(RoutePaths.adminCases),
          ),
        ],
      ),
    );
  }

  Widget _buildSviCard(CaseDetailModel d) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Stress Vulnerability Index (SVI)', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
              if (d.sviScore != null)
                Text(
                  '${d.sviScore!.toStringAsFixed(0)} / 100  (${d.riskCategory ?? "LOW"})',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.primary),
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (d.keyDrivers.isNotEmpty) ...[
            const Text('Key Drivers:', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
            const SizedBox(height: 4),
            Wrap(
              spacing: 8,
              children: d.keyDrivers.map((kd) => Chip(label: Text(kd, style: const TextStyle(fontSize: 11)))).toList(),
            ),
          ],
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.surfaceContainerLow,
              borderRadius: BorderRadius.circular(6),
            ),
            child: const Row(
              children: [
                Icon(Icons.info_outline, size: 16, color: AppColors.surfaceMutedText),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'AI-assisted vulnerability/risk triage indicator. Requires human review. Not a diagnostic tool.',
                    style: TextStyle(fontSize: 11, color: AppColors.surfaceMutedText),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAssessmentCard(CaseDetailModel d) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Structured AI Assessment (Gemma 3n E2B IT)', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          if (d.aiSummary != null)
            Text(d.aiSummary!, style: const TextStyle(fontSize: 13)),
          const SizedBox(height: 12),
          if (d.aiIndicators.isNotEmpty) ...[
            const Text('Indicators & Observations:', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            ...d.aiIndicators.map((ind) {
              final cat = ind['category'] ?? 'Observation';
              final conf = ind['confidence'] != null ? '${((ind['confidence'] as num) * 100).toStringAsFixed(0)}%' : 'N/A';
              final ev = ind['evidence'] ?? '';
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.arrow_right, size: 18, color: AppColors.primary),
                    Expanded(
                      child: Text('$cat (Confidence: $conf): $ev', style: const TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
              );
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildConversationCard(CaseDetailModel d) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Conversation Review', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          if (d.messages.isEmpty)
            const Text('No conversation messages recorded.', style: TextStyle(fontSize: 12, color: AppColors.surfaceMutedText))
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: d.messages.length,
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemBuilder: (context, i) {
                final m = d.messages[i];
                final isVictim = m['sender_type'] == 'VICTIM';
                final src = m['input_source'] ?? 'TEXT';
                return Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: isVictim ? AppColors.surfaceContainerLow : AppColors.surfaceContainer,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            isVictim ? 'Victim ($src)' : 'AI Sanctuary Assistant',
                            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                          ),
                          Text(
                            m['timestamp']?.toString().substring(11, 16) ?? '',
                            style: const TextStyle(fontSize: 10, color: AppColors.surfaceMutedText),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(m['content'] ?? '', style: const TextStyle(fontSize: 13)),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildRecommendationsCard(CaseDetailModel d) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Support Recommendations & Human Review', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          if (d.recommendations.isEmpty)
            const Text('No recommendations generated.', style: TextStyle(fontSize: 12, color: AppColors.surfaceMutedText))
          else
            ...d.recommendations.map((r) {
              return Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.surfaceContainerLow,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(r.category, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: r.status == 'PENDING' ? Colors.amber.withValues(alpha: 0.2) : Colors.green.withValues(alpha: 0.2),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(r.status, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(r.reason, style: const TextStyle(fontSize: 12)),
                    const SizedBox(height: 8),
                    Text('Action: ${r.responderAction}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                    if (r.responderNote != null) ...[
                      const SizedBox(height: 4),
                      Text('Admin Note: ${r.responderNote}', style: const TextStyle(fontSize: 11, fontStyle: FontStyle.italic)),
                    ],
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        FilledButton.tonal(
                          style: FilledButton.styleFrom(visualDensity: VisualDensity.compact),
                          onPressed: () => _handleDecision(r.id, 'ACCEPT'),
                          child: const Text('Accept'),
                        ),
                        const SizedBox(width: 8),
                        OutlinedButton(
                          style: OutlinedButton.styleFrom(visualDensity: VisualDensity.compact),
                          onPressed: () => _handleDecision(r.id, 'MODIFY'),
                          child: const Text('Modify'),
                        ),
                        const SizedBox(width: 8),
                        TextButton(
                          style: TextButton.styleFrom(visualDensity: VisualDensity.compact, foregroundColor: AppColors.error),
                          onPressed: () => _handleDecision(r.id, 'REJECT'),
                          child: const Text('Reject'),
                        ),
                      ],
                    ),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }

  Widget _buildAuditHistoryCard(CaseDetailModel d) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surfaceContainerLowest,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Append-Only Audit History', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          if (d.auditHistory.isEmpty)
            const Text('No audit records for this case.', style: TextStyle(fontSize: 12, color: AppColors.surfaceMutedText))
          else
            ...d.auditHistory.map((a) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Text(
                      a.createdAt.toLocal().toString().substring(11, 16),
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.surfaceMutedText),
                    ),
                    const SizedBox(width: 10),
                    Text(a.actorType, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    const SizedBox(width: 8),
                    Text(a.eventType, style: const TextStyle(fontSize: 11, color: AppColors.primary)),
                  ],
                ),
              );
            }),
        ],
      ),
    );
  }
}

// =============================================================================
// 4. ADMIN AUDIT LOG PAGE
// =============================================================================

class AdminAuditPage extends StatefulWidget {
  const AdminAuditPage({super.key});

  @override
  State<AdminAuditPage> createState() => _AdminAuditPageState();
}

class _AdminAuditPageState extends State<AdminAuditPage> {
  List<AdminAuditItemModel> _auditLogs = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchAudit();
  }

  Future<void> _fetchAudit() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final logs = await ResponderApiService.instance.fetchAdminAudit();
      if (mounted) {
        setState(() {
          _auditLogs = logs;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e is ApiException ? e.userMessage : 'Failed to retrieve audit log.';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AdminShellLayout(
      currentPath: RoutePaths.adminAudit,
      title: 'Audit Log',
      breadcrumb: 'Admin / Audit Log',
      onRefresh: _fetchAudit,
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Container(
          decoration: BoxDecoration(
            color: AppColors.surfaceContainerLowest,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
          ),
          child: _buildBody(),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_errorMessage!, style: const TextStyle(color: AppColors.error)),
            const SizedBox(height: 12),
            FilledButton.tonal(onPressed: _fetchAudit, child: const Text('Retry')),
          ],
        ),
      );
    }

    if (_auditLogs.isEmpty) {
      return const Center(child: Text('No audit records found.', style: TextStyle(color: AppColors.surfaceMutedText)));
    }

    return ListView.separated(
      itemCount: _auditLogs.length,
      separatorBuilder: (_, _) => Divider(height: 1, color: AppColors.outlineVariant.withValues(alpha: 0.2)),
      itemBuilder: (context, index) {
        final a = _auditLogs[index];
        return ListTile(
          dense: true,
          leading: const Icon(Icons.history, size: 20, color: AppColors.primary),
          title: Row(
            children: [
              Text(
                '${a.timestamp.hour.toString().padLeft(2, '0')}:${a.timestamp.minute.toString().padLeft(2, '0')}',
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
              ),
              const SizedBox(width: 10),
              Text(a.actorType, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
              const SizedBox(width: 10),
              Text(a.event, style: const TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.w600)),
            ],
          ),
          subtitle: Text('Entity: ${a.entity}  ${a.caseReference != null ? "•  Case: ${a.caseReference}" : ""}'),
        );
      },
    );
  }
}

// =============================================================================
// 5. ADMIN SETTINGS / SYSTEM INFO PAGE
// =============================================================================

class AdminSettingsPage extends StatelessWidget {
  const AdminSettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return AdminShellLayout(
      currentPath: RoutePaths.adminSettings,
      title: 'Settings & System Info',
      breadcrumb: 'Admin / Settings',
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainerLowest,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Role Configuration (LOCKED)', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),
                  const Text('Strict 2-Role RBAC Model:'),
                  const SizedBox(height: 6),
                  const Row(
                    children: [
                      Chip(label: Text('1. PEOPLE')),
                      SizedBox(width: 8),
                      Chip(label: Text('2. ADMIN')),
                    ],
                  ),
                  const SizedBox(height: 14),
                  const Divider(),
                  const SizedBox(height: 14),
                  const Text('Active AI Pipeline Models:', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  const Text('• ASR: ai4bharat/indic-conformer-600m-multilingual'),
                  const Text('• Speech Emotion: Dpngtm/wav2vec2-emotion-recognition'),
                  const Text('• Text Emotion: SamLowe/roberta-base-go_emotions'),
                  const Text('• Stress Detection: jtvallente/mentalbert_dreaddit_best'),
                  const Text('• Multimodal LLM: google/gemma-3n-E2B-it'),
                  const Text('• SVI Engine: Deterministic Formula v1.0'),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
