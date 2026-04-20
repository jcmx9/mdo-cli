import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';

/// Provider für die installierte Template-Version.
final templateVersionProvider = FutureProvider<String?>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return null;
  return engine.getTemplateVersion();
});

/// Provider für den Font-Status.
final fontStatusProvider =
    FutureProvider<Map<String, dynamic>>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return {'installed': false, 'missing': <String>[]};
  return engine.checkFonts();
});
