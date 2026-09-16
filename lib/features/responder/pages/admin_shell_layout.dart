import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/routes/route_paths.dart';
import '../../../core/theme/app_colors.dart';
import '../data/services/responder_api_service.dart';

/// Desktop-first responsive layout shell for the NHAA Admin Web Dashboard.
///
/// Implements:
/// - Left Sidebar: Logo, Navigation (Dashboard, Cases, Assessments, SVI, Recommendations, Audit, Settings), Profile & Logout.
/// - Top Header: Page title, Breadcrumb, Notification badge, Admin user & Role info, Dropdown menu.
/// - Main Content Area: Responsive container with Warm Ivory styling.
class AdminShellLayout extends StatelessWidget {
  final String currentPath;
  final String title;
  final String? breadcrumb;
  final Widget child;
  final VoidCallback? onRefresh;

  const AdminShellLayout({
    super.key,
    required this.currentPath,
    required this.title,
    this.breadcrumb,
    required this.child,
    this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isDesktop = constraints.maxWidth >= 900;

        if (isDesktop) {
          return Scaffold(
            backgroundColor: AppColors.background,
            body: Row(
              children: [
                // Left persistent sidebar
                SizedBox(
                  width: 250,
                  child: _buildSidebarContent(context),
                ),
                VerticalDivider(
                  width: 1,
                  thickness: 1,
                  color: AppColors.outlineVariant.withValues(alpha: 0.5),
                ),
                // Main right pane: Header + Content
                Expanded(
                  child: Column(
                    children: [
                      _buildHeader(context, isDesktop: true),
                      Divider(
                        height: 1,
                        thickness: 1,
                        color: AppColors.outlineVariant.withValues(alpha: 0.4),
                      ),
                      Expanded(
                        child: child,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }

        // Tablet & Mobile layout with Drawer
        return Scaffold(
          backgroundColor: AppColors.background,
          appBar: PreferredSize(
            preferredSize: const Size.fromHeight(60),
            child: _buildHeader(context, isDesktop: false),
          ),
          drawer: Drawer(
            child: _buildSidebarContent(context),
          ),
          body: child,
        );
      },
    );
  }

  Widget _buildSidebarContent(BuildContext context) {
    return Container(
      color: AppColors.surfaceContainerLow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Project Identity
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
            child: Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.shield_outlined,
                      color: Colors.white,
                      size: 22,
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        'NHAA 14566',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                              fontWeight: FontWeight.w700,
                              color: AppColors.primary,
                              letterSpacing: 0.5,
                            ),
                      ),
                      Text(
                        'Admin Operations',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontSize: 11,
                              color: AppColors.onSurfaceVariant,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          Divider(
            height: 1,
            thickness: 1,
            color: AppColors.outlineVariant.withValues(alpha: 0.3),
          ),

          // Primary Navigation Items
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
              children: [
                _buildNavItem(
                  context,
                  title: 'Overview',
                  icon: Icons.dashboard_outlined,
                  route: RoutePaths.adminDashboard,
                  isActive: currentPath == RoutePaths.adminDashboard,
                ),
                _buildNavItem(
                  context,
                  title: 'Cases',
                  icon: Icons.folder_shared_outlined,
                  route: RoutePaths.adminCases,
                  isActive: currentPath.startsWith(RoutePaths.adminCases),
                ),
                _buildNavItem(
                  context,
                  title: 'Assessments',
                  icon: Icons.psychology_outlined,
                  route: RoutePaths.adminAssessments,
                  isActive: currentPath == RoutePaths.adminAssessments,
                ),
                _buildNavItem(
                  context,
                  title: 'SVI & Risk',
                  icon: Icons.analytics_outlined,
                  route: RoutePaths.adminSviRisk,
                  isActive: currentPath == RoutePaths.adminSviRisk,
                ),
                _buildNavItem(
                  context,
                  title: 'Recommendations',
                  icon: Icons.verified_outlined,
                  route: RoutePaths.adminRecommendations,
                  isActive: currentPath == RoutePaths.adminRecommendations,
                ),
                _buildNavItem(
                  context,
                  title: 'Audit Log',
                  icon: Icons.history_edu_outlined,
                  route: RoutePaths.adminAudit,
                  isActive: currentPath == RoutePaths.adminAudit,
                ),
                const SizedBox(height: 12),
                Divider(
                  height: 1,
                  thickness: 1,
                  color: AppColors.outlineVariant.withValues(alpha: 0.3),
                ),
                const SizedBox(height: 12),
                _buildNavItem(
                  context,
                  title: 'Settings',
                  icon: Icons.settings_outlined,
                  route: RoutePaths.adminSettings,
                  isActive: currentPath == RoutePaths.adminSettings,
                ),
              ],
            ),
          ),

          // Bottom Admin Profile & Logout
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surfaceContainer,
              border: Border(
                top: BorderSide(
                  color: AppColors.outlineVariant.withValues(alpha: 0.3),
                ),
              ),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.primarySage,
                  child: const Text(
                    'AD',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        ResponderApiService.instance.session?.displayName ?? 'Admin User',
                        style: Theme.of(context).textTheme.labelMedium?.copyWith(
                              fontWeight: FontWeight.w600,
                            ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        'Role: ADMIN',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              fontSize: 10,
                              color: AppColors.primary,
                              fontWeight: FontWeight.w500,
                            ),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.logout, size: 18),
                  tooltip: 'Logout',
                  color: AppColors.onSurfaceVariant,
                  onPressed: () => _handleLogout(context),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem(
    BuildContext context, {
    required String title,
    required IconData icon,
    required String route,
    required bool isActive,
  }) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () {
            if (!isActive) {
              context.go(route);
            }
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: isActive ? AppColors.primary.withValues(alpha: 0.12) : Colors.transparent,
              borderRadius: BorderRadius.circular(8),
              border: isActive
                  ? Border.all(
                      color: AppColors.primary.withValues(alpha: 0.3),
                      width: 1,
                    )
                  : null,
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  size: 20,
                  color: isActive ? AppColors.primary : AppColors.onSurfaceVariant,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: theme.textTheme.labelMedium?.copyWith(
                      color: isActive ? AppColors.primary : AppColors.onSurface,
                      fontWeight: isActive ? FontWeight.w600 : FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, {required bool isDesktop}) {
    return Container(
      height: 60,
      color: AppColors.surfaceContainerLowest,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        children: [
          if (!isDesktop)
            IconButton(
              icon: const Icon(Icons.menu),
              onPressed: () => Scaffold.of(context).openDrawer(),
            ),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                      color: AppColors.onSurface,
                    ),
              ),
              if (breadcrumb != null)
                Text(
                  breadcrumb!,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontSize: 11,
                        color: AppColors.onSurfaceVariant,
                      ),
                ),
            ],
          ),
          const Spacer(),
          // Confidentiality & Synthetic Demo Indicator
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.secondaryContainer.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.secondary.withValues(alpha: 0.2)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.shield, size: 12, color: AppColors.secondary),
                const SizedBox(width: 5),
                Text(
                  'DEMO / SYNTHETIC DATA',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: AppColors.onSecondaryContainer,
                    letterSpacing: 0.3,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          // Refresh Button
          if (onRefresh != null)
            IconButton(
              icon: const Icon(Icons.refresh, size: 20),
              tooltip: 'Reload Data',
              color: AppColors.onSurfaceVariant,
              onPressed: onRefresh,
            ),
          const SizedBox(width: 8),
          // Admin Menu Dropdown
          PopupMenuButton<String>(
            tooltip: 'Admin Profile Menu',
            offset: const Offset(0, 45),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                CircleAvatar(
                  radius: 15,
                  backgroundColor: AppColors.primary,
                  child: const Text(
                    'A',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'Administrator',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        fontWeight: FontWeight.w600,
                        color: AppColors.onSurface,
                      ),
                ),
                const Icon(Icons.arrow_drop_down, size: 18),
              ],
            ),
            onSelected: (val) {
              if (val == 'settings') {
                context.go(RoutePaths.adminSettings);
              } else if (val == 'logout') {
                _handleLogout(context);
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'settings',
                child: Row(
                  children: [
                    Icon(Icons.person_outline, size: 18),
                    SizedBox(width: 10),
                    Text('Profile & System Info'),
                  ],
                ),
              ),
              const PopupMenuDivider(),
              const PopupMenuItem(
                value: 'logout',
                child: Row(
                  children: [
                    Icon(Icons.logout, size: 18, color: AppColors.tertiary),
                    SizedBox(width: 10),
                    Text('Logout', style: TextStyle(color: AppColors.tertiary)),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _handleLogout(BuildContext context) {
    ResponderApiService.instance.logout();
    context.go(RoutePaths.adminLogin);
  }
}
