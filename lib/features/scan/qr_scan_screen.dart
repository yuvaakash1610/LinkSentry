import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/constants/app_typography.dart';
import '../../core/widgets/app_button.dart';
import '../../state/app_state_provider.dart';
import '../result/result_screen.dart';

class QrScanScreen extends StatefulWidget {
  const QrScanScreen({super.key});

  @override
  State<QrScanScreen> createState() => _QrScanScreenState();
}

class _QrScanScreenState extends State<QrScanScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _animController;
  bool _isFlashOn = false;
  bool _isSimulatingScan = false;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  void _onQrDetected(String rawPayload) async {
    if (_isSimulatingScan) return;
    setState(() => _isSimulatingScan = true);

    final state = Provider.of<AppStateProvider>(context, listen: false);
    final result = await state.analyzeUrl(rawPayload);

    if (mounted) {
      if (result != null) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => const ResultScreen(),
          ),
        );
      } else {
        setState(() => _isSimulatingScan = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        elevation: 0,
        title: const Text('QR Safety Checkpoint'),
        actions: [
          IconButton(
            icon: Icon(
              _isFlashOn ? Icons.flash_on_rounded : Icons.flash_off_rounded,
              color: Colors.white,
            ),
            onPressed: () {
              setState(() => _isFlashOn = !_isFlashOn);
            },
          ),
        ],
      ),
      body: Stack(
        children: [
          // Simulated Camera Preview Viewport
          Container(
            width: double.infinity,
            height: double.infinity,
            color: const Color(0xFF121212),
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.camera_alt_outlined,
                    size: 64,
                    color: Colors.white24,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Point camera at a QR code',
                    style: AppTypography.bodyMedium.copyWith(
                      color: Colors.white70,
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Scanning Target Viewfinder Overlay Frame
          Center(
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(24),
                border: Border.all(
                  color: AppColors.onPrimaryContainer,
                  width: 3,
                ),
              ),
              child: Stack(
                children: [
                  // Animated Scanning Laser Line
                  AnimatedBuilder(
                    animation: _animController,
                    builder: (context, child) {
                      return Positioned(
                        top: _animController.value * 240,
                        left: 10,
                        right: 10,
                        child: Container(
                          height: 3,
                          decoration: BoxDecoration(
                            color: AppColors.onPrimaryContainer,
                            boxShadow: [
                              BoxShadow(
                                color: AppColors.onPrimaryContainer
                                    .withValues(alpha: 0.8),
                                blurRadius: 10,
                                spreadRadius: 2,
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),

          // Bottom Controls & Safety Guarantee
          Positioned(
            bottom: 30,
            left: 20,
            right: 20,
            child: Column(
              children: [
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.75),
                    borderRadius: BorderRadius.circular(9999),
                    border: Border.all(color: Colors.white24),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.shield_outlined,
                        color: Color(0xFF69F0AE),
                        size: 18,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'LinkSentry will never auto-open QR URLs',
                        style: AppTypography.bodySmall.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                AppButton(
                  label: _isSimulatingScan
                      ? 'Analyzing QR Code...'
                      : 'Simulate QR Code Scan',
                  icon: Icons.qr_code_scanner_rounded,
                  isLoading: _isSimulatingScan,
                  onPressed: () {
                    _onQrDetected('https://sbi-secure-kyc-update.cc/verify');
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
