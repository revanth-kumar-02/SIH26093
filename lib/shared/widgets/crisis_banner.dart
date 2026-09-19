import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/constants/app_strings.dart';
import '../../core/theme/app_colors.dart';

/// Trauma-informed crisis helpline banner.
///
/// Direct replication of the terracotta urgent safety bar in the approved Stitch designs.
class CrisisBanner extends StatelessWidget {
  const CrisisBanner({
    super.key,
    this.showDualEmergency = false,
  });

  /// When true, renders both 14566 Helpline and 112 Emergency options (as in Screen 8).
  final bool showDualEmergency;

  Future<void> _launchDialer(BuildContext context, String number) async {
    final uri = Uri.parse('tel:$number');
    try {
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri);
      } else {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Please dial $number from your phone.'),
              backgroundColor: AppColors.tertiary,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Please dial $number from your phone.'),
            backgroundColor: AppColors.tertiary,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  void _showHelplineDialog(BuildContext context, String number, String label) {
    showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surfaceContainerLowest,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.tertiaryFixed,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.phone_in_talk, color: AppColors.tertiary, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'You are connecting to Emergency Helpline ($number).',
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: AppColors.onSurface, height: 1.4),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainerLow,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
              ),
              child: const Text(
                AppStrings.demoDisclaimer,
                style: TextStyle(fontSize: 12, color: AppColors.onSurfaceVariant, height: 1.4),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel', style: TextStyle(color: AppColors.onSurfaceVariant)),
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.tertiary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            onPressed: () {
              Navigator.of(ctx).pop();
              _launchDialer(context, number);
            },
            child: Text('Dial $number'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (showDualEmergency) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.errorContainer.withValues(alpha: 0.35),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.outlineVariant.withValues(alpha: 0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: const BoxDecoration(
                    color: AppColors.tertiaryContainer,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.emergency_outlined, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Need instant protection?',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppColors.onSurface,
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'If your physical safety is in danger right now, bypass this intake.',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.onSurfaceVariant,
                          height: 1.3,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 46,
                    child: FilledButton.icon(
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.tertiary,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        elevation: 1,
                      ),
                      onPressed: () => _showHelplineDialog(
                        context,
                        AppStrings.emergencyContactNumber,
                        AppStrings.demoSupportLabel,
                      ),
                      icon: const Icon(Icons.call, size: 16),
                      label: Text(
                        AppStrings.tr('demo_support'),
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SizedBox(
                    height: 46,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        backgroundColor: AppColors.surfaceContainerLowest,
                        foregroundColor: AppColors.onSurface,
                        side: BorderSide(color: AppColors.outlineVariant.withValues(alpha: 0.5)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: () => _showHelplineDialog(
                        context,
                        AppStrings.womenHelplineNumber,
                        AppStrings.demoEmergencyLabel,
                      ),
                      icon: const Icon(Icons.support_agent, size: 16, color: AppColors.onSurface),
                      label: Text(
                        AppStrings.tr('demo_line'),
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      );
    }

    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () => _showHelplineDialog(
        context,
        AppStrings.emergencyContactNumber,
        AppStrings.demoSupportLabel,
      ),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: AppColors.tertiaryFixed.withValues(alpha: 0.45),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.tertiaryFixedDim.withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: const BoxDecoration(
                color: AppColors.tertiary,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.phone_in_talk, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    AppStrings.tr('crisis_banner_title'),
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.onTertiaryFixed,
                    ),
                  ),
                  const SizedBox(height: 1),
                  Text(
                    '${AppStrings.tr('crisis_banner_sub')}: ${AppStrings.demoContactNumber}',
                    style: const TextStyle(
                      fontSize: 11.5,
                      color: AppColors.onTertiaryFixedVariant,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  AppStrings.tr('demo_call'),
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: AppColors.tertiary,
                  ),
                ),
                const SizedBox(width: 4),
                const Icon(Icons.arrow_forward, size: 14, color: AppColors.tertiary),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

