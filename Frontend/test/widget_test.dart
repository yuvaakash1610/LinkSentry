import 'package:flutter_test/flutter_test.dart';
import 'package:linksentry/app/app.dart';

void main() {
  testWidgets('LinkSentry initial app render test', (WidgetTester tester) async {
    await tester.pumpWidget(const LinkSentryApp());
    await tester.pumpAndSettle();

    expect(find.text('LinkSentry'), findsWidgets);
    expect(find.text('Think before you tap.'), findsWidgets);
    expect(find.text('Get Started'), findsOneWidget);
  });
}
