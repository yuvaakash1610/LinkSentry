import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/app_strings.dart';
import '../state/app_state_provider.dart';
import '../features/onboarding/onboarding_screen.dart';
import '../features/navigation/main_navigation_screen.dart';
import 'routes.dart';
import 'theme.dart';

class LinkSentryApp extends StatelessWidget {
  const LinkSentryApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppStateProvider(),
      child: Consumer<AppStateProvider>(
        builder: (context, state, _) {
          return MaterialApp(
            title: AppStrings.appName,
            debugShowCheckedModeBanner: false,
            theme: AppTheme.lightTheme,
            home: state.isOnboardingCompleted
                ? const MainNavigationScreen()
                : const OnboardingScreen(),
            routes: AppRoutes.routes,
          );
        },
      ),
    );
  }
}
