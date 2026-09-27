import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/empty_state.dart';
import '../../core/widgets/history_card.dart';
import '../../state/app_state_provider.dart';
import '../result/result_screen.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  String _searchQuery = '';

  void _showClearConfirmation(BuildContext context, AppStateProvider state) {
    showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('Clear Scan History?'),
        content: const Text(
          'This will permanently delete all scan summaries saved on this device. This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogCtx).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.error,
              foregroundColor: Colors.white,
            ),
            onPressed: () {
              state.clearAllHistory();
              Navigator.of(dialogCtx).pop();
            },
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStateProvider>(
      builder: (context, state, _) {
        final filteredHistory = state.history.where((item) {
          if (_searchQuery.isEmpty) return true;
          final query = _searchQuery.toLowerCase();
          return item.title.toLowerCase().contains(query) ||
              (item.domain != null && item.domain!.toLowerCase().contains(query));
        }).toList();

        return Scaffold(
          backgroundColor: AppColors.surface,
          appBar: AppBar(
            title: const Text('Scan History'),
            backgroundColor: AppColors.surface,
            elevation: 0,
            actions: [
              if (state.history.isNotEmpty)
                IconButton(
                  icon: const Icon(Icons.delete_sweep_outlined),
                  color: AppColors.error,
                  tooltip: 'Clear All History',
                  onPressed: () => _showClearConfirmation(context, state),
                ),
            ],
          ),
          body: SafeArea(
            child: Column(
              children: [
                // Search Input Well
                if (state.history.isNotEmpty)
                  Padding(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceContainerLow,
                        borderRadius: BorderRadius.circular(9999),
                        border: Border.all(color: AppColors.surfaceContainerHigh),
                      ),
                      child: TextField(
                        onChanged: (val) => setState(() => _searchQuery = val),
                        style: AppTypography.bodyMedium.copyWith(
                          color: AppColors.onSurface,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Search past scans or domains...',
                          hintStyle: AppTypography.bodyMedium.copyWith(
                            color: AppColors.outline,
                          ),
                          prefixIcon: const Icon(Icons.search_rounded,
                              size: 20, color: AppColors.outline),
                          border: InputBorder.none,
                          isDense: true,
                        ),
                      ),
                    ),
                  ),

                // History List / Empty State
                Expanded(
                  child: filteredHistory.isEmpty
                      ? EmptyState(
                          icon: Icons.history_rounded,
                          title: state.history.isEmpty
                              ? 'No Scan History Yet'
                              : 'No Matching Scans Found',
                          description: state.history.isEmpty
                              ? 'Scans you analyze will be stored locally on your device for quick reference.'
                              : 'Try adjusting your search keywords.',
                          buttonLabel: state.history.isEmpty
                              ? 'Perform First Scan'
                              : null,
                          onButtonTap: () {
                            state.setTabIndex(1); // Go to Scan tab
                          },
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 8),
                          itemCount: filteredHistory.length,
                          itemBuilder: (context, index) {
                            final item = filteredHistory[index];
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 10),
                              child: HistoryCard(
                                item: item,
                                onTap: () {
                                  if (item.domain != null) {
                                    state.analyzeUrl('https://${item.domain}');
                                  } else {
                                    state.analyzeText(item.title);
                                  }
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => const ResultScreen(),
                                    ),
                                  );
                                },
                                onDelete: () =>
                                    state.deleteHistoryItem(item.id),
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
