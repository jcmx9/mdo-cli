import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/engine/mdo_engine.dart';

/// Notifier für die MdoEngine-Instanz.
class EngineNotifier extends Notifier<MdoEngine?> {
  @override
  MdoEngine? build() => null;

  void setEngine(MdoEngine engine) {
    state = engine;
  }
}

/// Provider für die MdoEngine-Instanz.
final engineProvider =
    NotifierProvider<EngineNotifier, MdoEngine?>(EngineNotifier.new);
