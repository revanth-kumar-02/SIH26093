import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/routes/route_paths.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/crisis_banner.dart';
import '../../../../shared/widgets/sanctuary_bottom_nav.dart';
import '../../../../shared/widgets/sanctuary_header.dart';

/// Support & Emergency Page — Phase C implementation.
///
/// Implements the care recommendations and emergency support hierarchy while
/// maintaining the approved Sage Green, Soft Olive, and Muted Terracotta visual identity.
class SupportEmergencyPage extends StatefulWidget {
  const SupportEmergencyPage({super.key});

  @override
  State<SupportEmergencyPage> createState() => _SupportEmergencyPageState();
}

class _SupportEmergencyPageState extends State<SupportEmergencyPage> {
  int _navIndex = 2; // Care & Help active tab

  void _onBottomNavTapped(int index) {
    if (index == 3) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Safe Vault is coming soon.'),
          behavior: SnackBarBehavior.floating,
          duration: Duration(seconds: 2),
        ),
      );
      return;
    }
    setState(() => _navIndex = index);
    if (index == 0) {
      context.go(RoutePaths.home);
    } else if (index == 1) {
      context.go(RoutePaths.aiChat);
    }
  }

  void _showResourceDetails(String title, String description) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
        content: Text(
          description,
          style: const TextStyle(fontSize: 13.5, color: AppColors.onSurfaceVariant, height: 1.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Close'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('Request logged for $title. An advocate will assist shortly.'),
                  backgroundColor: AppColors.primary,
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: const Text('Request Connection'),
          ),
        ],
      ),
    );
  }

  void _performQuickExit() {
    // Discreetly navigate back to home and show reassurance
    context.go(RoutePaths.home);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.surface,
      appBar: SanctuaryHeader(
        title: 'Care & Emergency',
        subtitle: 'TRUEVOICE',
        showBack: true,
        onBack: () => context.go(RoutePaths.home),
      ),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 480),
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
              children: [
                // Top Emergency Protection Banner (Dual 14566 & 112)
                const CrisisBanner(showDualEmergency: true),
                const SizedBox(height: 18),

                // Assigned Human Advocate Care Pathway Card
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceContainerLowest,
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.03),
                        blurRadius: 10,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            width: 38,
                            height: 38,
                            decoration: const BoxDecoration(
                              color: AppColors.primaryFixed,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.support_agent,
                              size: 22,
                              color: AppColors.onPrimaryFixedVariant,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Dedicated Human Advocate',
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.onSurface,
                                  ),
                                ),
                                const SizedBox(height: 1),
                                Text(
                                  'NHAA Priority Response Team',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: AppColors.onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(999),
                            ),
                            child: const Text(
                              'Assigned',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: AppColors.primary,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Your intake has been securely staged. A certified trauma-informed counselor is available to guide your next steps with total confidentiality.',
                        style: TextStyle(
                          fontSize: 12.5,
                          height: 1.45,
                          color: AppColors.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Section: Supportive Care Options
                Text(
                  'Supportive Care Pathways',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontSize: 17,
                        fontWeight: FontWeight.w600,
                        color: AppColors.onSurface,
                      ),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Choose the assistance you feel most ready to receive right now.',
                  style: TextStyle(
                    fontSize: 13,
                    color: AppColors.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: 14),

                // Option 1: Crisis Counseling
                _buildSupportOptionCard(
                  icon: Icons.forum_outlined,
                  title: 'Immediate Crisis Counseling',
                  subtitle: '24/7 one-on-one confidential talk or text with certified counselors.',
                  badge: 'Available 24/7',
                  badgeBg: AppColors.secondaryContainer,
                  badgeColor: AppColors.onSecondaryContainer,
                  onTap: () => _showResourceDetails(
                    'Immediate Crisis Counseling',
                    'Connect with a certified NHAA counselor. You can discuss what occurred in a safe, judgment-free space with complete legal and privacy protections.',
                  ),
                ),
                const SizedBox(height: 10),

                // Option 2: Safe Shelter
                _buildSupportOptionCard(
                  icon: Icons.home_work_outlined,
                  title: 'Safe Shelter & Accommodation',
                  subtitle: 'Confidential verified emergency lodging and immediate hostel relocation.',
                  badge: 'Emergency Relocation',
                  badgeBg: AppColors.surfaceContainerHigh,
                  badgeColor: AppColors.onSurface,
                  onTap: () => _showResourceDetails(
                    'Safe Shelter & Accommodation',
                    'If your current accommodation is compromised, NHAA coordinates immediate, secure, and private emergency lodging guidance.',
                  ),
                ),
                const SizedBox(height: 10),

                // Option 3: Legal Guidance
                _buildSupportOptionCard(
                  icon: Icons.gavel_outlined,
                  title: 'Confidential Legal Guidance',
                  subtitle: 'Support with protective orders, zero-FIR filing, and rights advocacy.',
                  badge: 'Advocate Legal Aid',
                  badgeBg: AppColors.surfaceContainerHigh,
                  badgeColor: AppColors.onSurface,
                  onTap: () => _showResourceDetails(
                    'Confidential Legal Guidance',
                    'Access pro bono victim advocates and legal specialists who can assist with documentation and official filings without pressuring you.',
                  ),
                ),
                const SizedBox(height: 10),

                // Option 4: Anonymous Formal Report
                _buildSupportOptionCard(
                  icon: Icons.fingerprint,
                  title: 'Anonymous Digital Intake',
                  subtitle: 'Preserve formal incident testimony with cryptographic privacy.',
                  badge: 'Cryptographic Privacy',
                  badgeBg: AppColors.surfaceContainerHigh,
                  badgeColor: AppColors.onSurface,
                  onTap: () => _showResourceDetails(
                    'Anonymous Digital Intake',
                    'Your statements can be verified and saved with cryptographic timestamping, allowing you to present them whenever you are ready.',
                  ),
                ),
                const SizedBox(height: 20),

                // Quick Exit Button for Victim Safety
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.onSurfaceVariant,
                      side: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.4)),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onPressed: _performQuickExit,
                    icon: const Icon(Icons.close, size: 18),
                    label: const Text(
                      'Quick Exit (Return to TrueVoice)',
                      style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
      bottomNavigationBar: SanctuaryBottomNav(
        currentIndex: _navIndex,
        onTap: _onBottomNavTapped,
      ),
    );
  }

  Widget _buildSupportOptionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required String badge,
    required Color badgeBg,
    required Color badgeColor,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surfaceContainerLowest,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.25)),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.secondaryContainer.withValues(alpha: 0.5),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, size: 20, color: AppColors.primary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          title,
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.onSurface,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                        decoration: BoxDecoration(
                          color: badgeBg,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          badge,
                          style: TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                            color: badgeColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 12,
                      height: 1.4,
                      color: AppColors.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            const Padding(
              padding: EdgeInsets.only(left: 8, top: 4),
              child: Icon(Icons.chevron_right, size: 18, color: AppColors.outline),
            ),
          ],
        ),
      ),
    );
  }
}
