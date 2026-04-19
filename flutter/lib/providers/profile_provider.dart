import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';

/// Provider für die Liste der Profilnamen.
final profileListProvider = FutureProvider<List<String>>((ref) async {
  final engine = ref.watch(engineProvider);
  if (engine == null) return [];
  return engine.listProfiles();
});
