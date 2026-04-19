import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/engine/mdo_engine.dart';

/// Provider für die MdoEngine-Instanz.
/// Wird gesetzt, sobald der Python-Server gestartet ist.
final engineProvider = StateProvider<MdoEngine?>((ref) => null);
