import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/app_typography.dart';

class AppButton extends StatelessWidget {
  final String label;
  final IconData? icon;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isFullWidth;
  final ButtonVariant variant;

  const AppButton({
    super.key,
    required this.label,
    this.icon,
    this.onPressed,
    this.isLoading = false,
    this.isFullWidth = true,
    this.variant = ButtonVariant.primary,
  });

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    Color fgColor;
    BorderSide border = BorderSide.none;

    switch (variant) {
      case ButtonVariant.primary:
        bgColor = AppColors.primaryContainer;
        fgColor = AppColors.onPrimary;
        break;
      case ButtonVariant.secondary:
        bgColor = AppColors.secondaryContainer;
        fgColor = AppColors.onSecondaryContainer;
        break;
      case ButtonVariant.tonal:
        bgColor = AppColors.secondaryFixed;
        fgColor = AppColors.onSecondaryFixed;
        break;
      case ButtonVariant.outlined:
        bgColor = Colors.transparent;
        fgColor = AppColors.secondary;
        border = BorderSide(
          color: AppColors.secondary.withValues(alpha: 0.3),
          width: 1.5,
        );
        break;
      case ButtonVariant.text:
        bgColor = Colors.transparent;
        fgColor = AppColors.primary;
        break;
    }

    final Widget child = isLoading
        ? SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2.5,
              valueColor: AlwaysStoppedAnimation<Color>(fgColor),
            ),
          )
        : Row(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 20, color: fgColor),
                const SizedBox(width: 8),
              ],
              Text(
                label,
                style: AppTypography.labelLarge.copyWith(
                  color: fgColor,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          );

    final Widget button = Material(
      color: bgColor,
      borderRadius: BorderRadius.circular(24),
      elevation: variant == ButtonVariant.primary ? 2 : 0,
      shadowColor: AppColors.primary.withValues(alpha: 0.12),
      child: InkWell(
        onTap: isLoading ? null : onPressed,
        borderRadius: BorderRadius.circular(24),
        child: Container(
          height: 52,
          padding: const EdgeInsets.symmetric(horizontal: 24),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(24),
            border: Border.fromBorderSide(border),
          ),
          alignment: Alignment.center,
          child: child,
        ),
      ),
    );

    if (isFullWidth) {
      return SizedBox(width: double.infinity, child: button);
    }

    return button;
  }
}

enum ButtonVariant { primary, secondary, tonal, outlined, text }
