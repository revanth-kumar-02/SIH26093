import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';
import '../data/models/responder_models.dart';
import '../data/services/responder_api_service.dart';

/// Screen 13: Case List
/// Filterable, searchable case queue with progressive disclosure of risk tiers, safety flags, and assignment statuses.
class CaseListPage extends StatefulWidget {
  const CaseListPage({super.key});

  @override
  State<CaseListPage> createState() => _CaseListPageState();
}

class _CaseListPageState extends State<CaseListPage> {
  final _searchController = TextEditingController();
  bool _isLoading = true;
  String? _error;
  List<CaseListItemModel> _cases = [];

  String? _selectedRisk;
  String? _selectedStatus;
  bool _assignedToMe = false;

  @override
  void initState() {
    super.initState();
    _fetchCases();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _fetchCases() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final cases = await ResponderApiService.instance.fetchCases(
        riskCategory: _selectedRisk,
        status: _selectedStatus,
        assignedToMe: _assignedToMe,
        search: _searchController.text.trim().isEmpty ? null : _searchController.text.trim(),
      );

      if (mounted) {
        setState(() {
          _cases = cases;
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Case Management Queue'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.go(RoutePaths.responderDashboard),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchCases,
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter & Search Controls Header
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              children: [
                // Search Input
                TextField(
                  controller: _searchController,
                  onSubmitted: (_) => _fetchCases(),
                  decoration: InputDecoration(
                    hintText: 'Search safe case reference (e.g. 0812)...',
                    prefixIcon: const Icon(Icons.search, size: 20),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _searchController.clear();
                              _fetchCases();
                            },
                          )
                        : null,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
                const SizedBox(height: 10),

                // Filter Chips Row
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      FilterChip(
                        label: const Text('All'),
                        selected: _selectedRisk == null && _selectedStatus == null && !_assignedToMe,
                        onSelected: (_) {
                          setState(() {
                            _selectedRisk = null;
                            _selectedStatus = null;
                            _assignedToMe = false;
                          });
                          _fetchCases();
                        },
                      ),
                      const SizedBox(width: 6),
                      FilterChip(
                        label: const Text('Assigned To Me'),
                        selected: _assignedToMe,
                        onSelected: (val) {
                          setState(() => _assignedToMe = val);
                          _fetchCases();
                        },
                      ),
                      const SizedBox(width: 6),
                      FilterChip(
                        label: const Text('Critical Risk'),
                        selected: _selectedRisk == 'CRITICAL',
                        selectedColor: AppColors.tertiary.withValues(alpha: 0.2),
                        onSelected: (val) {
                          setState(() => _selectedRisk = val ? 'CRITICAL' : null);
                          _fetchCases();
                        },
                      ),
                      const SizedBox(width: 6),
                      FilterChip(
                        label: const Text('High Risk'),
                        selected: _selectedRisk == 'HIGH',
                        selectedColor: Colors.amber.shade200,
                        onSelected: (val) {
                          setState(() => _selectedRisk = val ? 'HIGH' : null);
                          _fetchCases();
                        },
                      ),
                      const SizedBox(width: 6),
                      FilterChip(
                        label: const Text('New'),
                        selected: _selectedStatus == 'NEW',
                        onSelected: (val) {
                          setState(() => _selectedStatus = val ? 'NEW' : null);
                          _fetchCases();
                        },
                      ),
                      const SizedBox(width: 6),
                      FilterChip(
                        label: const Text('In Review'),
                        selected: _selectedStatus == 'IN_REVIEW',
                        onSelected: (val) {
                          setState(() => _selectedStatus = val ? 'IN_REVIEW' : null);
                          _fetchCases();
                        },
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Case List Content
          Expanded(
            child: _isLoading
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
                            FilledButton(onPressed: _fetchCases, child: const Text('Retry')),
                          ],
                        ),
                      )
                    : _cases.isEmpty
                        ? const Center(
                            child: Text(
                              'No matching cases found.',
                              style: TextStyle(color: AppColors.onSurfaceVariant),
                            ),
                          )
                        : ListView.builder(
                            padding: const EdgeInsets.all(16),
                            itemCount: _cases.length,
                            itemBuilder: (context, idx) => _buildCaseCard(_cases[idx]),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildCaseCard(CaseListItemModel c) {
    final riskColor = _getRiskColor(c.latestRiskCategory);

    return Card(
      elevation: 1.5,
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top Row: Ref ID + Urgent Flag + Risk Badge
            Row(
              children: [
                Expanded(
                  child: Row(
                    children: [
                      Text(
                        c.externalCaseReference,
                        style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                      ),
                      if (c.immediateSafetyAttention || c.urgentHumanReview) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.tertiary,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.warning, color: Colors.white, size: 10),
                              SizedBox(width: 4),
                              Text(
                                'URGENT SAFETY',
                                style: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: riskColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: riskColor.withValues(alpha: 0.4)),
                  ),
                  child: Text(
                    'SVI ${(c.latestSviScore ?? 0).toStringAsFixed(1)} • ${c.latestRiskCategory ?? "UNASSESSED"}',
                    style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12, color: riskColor),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Metadata row
            Wrap(
              spacing: 12,
              runSpacing: 6,
              children: [
                _buildMetaPill(Icons.flag_outlined, 'Status: ${c.status}'),
                _buildMetaPill(Icons.language, 'Language: ${c.language.toUpperCase()}'),
                _buildMetaPill(
                  Icons.person_pin_outlined,
                  'Assigned: ${c.assignedResponderName ?? "None"}',
                ),
                _buildMetaPill(
                  Icons.access_time,
                  'Updated: ${_formatDate(c.updatedAt)}',
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Action Button
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                FilledButton.tonal(
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.primary.withValues(alpha: 0.12),
                    foregroundColor: AppColors.primary,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: () => context.go('/responder/cases/${c.id}'),
                  child: const Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text('Review Triage Details', style: TextStyle(fontWeight: FontWeight.bold)),
                      SizedBox(width: 6),
                      Icon(Icons.arrow_forward, size: 16),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetaPill(IconData icon, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 13, color: AppColors.onSurfaceVariant),
        const SizedBox(width: 4),
        Text(text, style: const TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant)),
      ],
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
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
