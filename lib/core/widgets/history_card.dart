import 'package:flutter/material.dart';
import '../../models/scan_history_item.dart';
import '../../models/scan_request.dart';
import '../constants/app_colors.dart';
import '../constants/app_typography.dart';
import 'risk_badge.dart';

class HistoryCard extends StatelessWidget {
  final ScanHistoryItem item;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const HistoryCard({
    super.key,
    required this.item,
    required this.onTap,
    required this.onDelete,
  });

  IconData _getScanIcon(ScanType type) {
    switch (type) {
      case ScanType.text:
        return Icons.sms_outlined;
      case ScanType.url:
        return Icons.link_rounded;
      case ScanType.qr:
        return Icons.qr_code_scanner_rounded;
      case ScanType.notification:
        return Icons.notifications_active_outlined;
    }
  }

  String _formatTime(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 1) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surfaceContainerLowest,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.surfaceContainerHighest),
            boxShadow: AppColors.cardShadow,
          ),
          child: Row(
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: AppColors.secondaryContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  _getScanIcon(item.scanType),
                  color: AppColors.primary,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.titleMedium.copyWith(
                        fontSize: 15,
                        color: AppColors.onSurface,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        if (item.domain != null) ...[
                          Flexible(
                            child: Text(
                              item.domain!,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: AppTypography.bodySmall.copyWith(
                                color: AppColors.primaryContainer,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                          const Text('•', style: TextStyle(color: Colors.grey)),
                          const SizedBox(width: 6),
                        ],
                        Text(
                          _formatTime(item.timestamp),
                          style: AppTypography.bodySmall.copyWith(
                            color: AppColors.outline,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              RiskBadge(level: item.riskLevel),
              IconButton(
                icon: const Icon(Icons.close_rounded, size: 18),
                color: AppColors.outline,
                onPressed: onDelete,
                tooltip: 'Delete history entry',
              ),
            ],
          ),
        ),
      ),
    );
  }
}
