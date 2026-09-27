class UrlExtractor {
  UrlExtractor._();

  static final RegExp _urlRegex = RegExp(
    r'(https?:\/\/[^\s<]+[^<.,:;""]|www\.[^\s<]+[^<.,:;""])',
    caseSensitive: false,
  );

  /// Extract all URLs from a given string
  static List<String> extractUrls(String text) {
    if (text.isEmpty) return [];
    final matches = _urlRegex.allMatches(text);
    final urls = <String>[];
    for (final match in matches) {
      String url = match.group(0)!;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://$url';
      }
      if (!urls.contains(url)) {
        urls.add(url);
      }
    }
    return urls;
  }

  /// Extract host/domain name from a URL
  static String? extractDomain(String url) {
    try {
      String clean = url.trim();
      if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
        clean = 'https://$clean';
      }
      final uri = Uri.parse(clean);
      return uri.host.isNotEmpty ? uri.host : null;
    } catch (_) {
      return null;
    }
  }
}
