import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../state/app_state_provider.dart';
import '../home/home_dashboard_screen.dart';
import '../scan/scan_hub_screen.dart';
import '../history/history_screen.dart';
import '../learn/learn_screen.dart';
import '../settings/settings_screen.dart';

class MainNavigationScreen extends StatelessWidget {
  const MainNavigationScreen({super.key});

  static const List<Widget> _screens = [
    HomeDashboardScreen(),
    ScanHubScreen(),
    HistoryScreen(),
    LearnScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Consumer<AppStateProvider>(
      builder: (context, state, _) {
        final currentIndex = state.selectedTabIndex;

        return Scaffold(
          body: IndexedStack(
            index: currentIndex,
            children: _screens,
          ),
          bottomNavigationBar: Container(
            decoration: BoxDecoration(
              color: AppColors.surfaceContainerLowest,
              boxShadow: AppColors.floatingShadow,
              borderRadius: const BorderRadius.vertical(
                top: Radius.circular(24),
              ),
            ),
            child: SafeArea(
              child: NavigationBar(
                selectedIndex: currentIndex,
                onDestinationSelected: (index) {
                  state.setTabIndex(index);
                },
                backgroundColor: Colors.transparent,
                indicatorColor: AppColors.secondaryFixed,
                elevation: 0,
                destinations: const [
                  NavigationDestination(
                    icon: Icon(Icons.home_outlined),
                    selectedIcon: Icon(Icons.home_rounded, color: AppColors.onSecondaryFixed),
                    label: 'Home',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.qr_code_scanner_outlined),
                    selectedIcon: Icon(Icons.qr_code_scanner_rounded, color: AppColors.onSecondaryFixed),
                    label: 'Scan',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.history_outlined),
                    selectedIcon: Icon(Icons.history_rounded, color: AppColors.onSecondaryFixed),
                    label: 'History',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.school_outlined),
                    selectedIcon: Icon(Icons.school_rounded, color: AppColors.onSecondaryFixed),
                    label: 'Learn',
                  ),
                  NavigationDestination(
                    icon: Icon(Icons.settings_outlined),
                    selectedIcon: Icon(Icons.settings_rounded, color: AppColors.onSecondaryFixed),
                    label: 'Settings',
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
