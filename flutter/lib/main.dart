import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:serious_python/serious_python.dart';

import 'package:mdo_app/app.dart';
import 'package:mdo_app/engine/mdo_engine.dart';
import 'package:mdo_app/providers/engine_provider.dart';

void main() {
  runApp(
    const ProviderScope(
      child: _AppLoader(),
    ),
  );
}

/// Pfad zum Resources-Verzeichnis im macOS App-Bundle.
String _resourcesDir() {
  final execDir = File(Platform.resolvedExecutable).parent.path;
  return '${Directory(execDir).parent.path}/Resources';
}

class _AppLoader extends ConsumerStatefulWidget {
  const _AppLoader();

  @override
  ConsumerState<_AppLoader> createState() => _AppLoaderState();
}

class _AppLoaderState extends ConsumerState<_AppLoader> {
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _startPythonServer();
  }

  Future<void> _startPythonServer() async {
    try {
      // Pfad zu gebündelten Binaries (typst, pandoc)
      final binPath = _resourcesDir();

      await SeriousPython.run(
        'app/app.zip',
        environmentVariables: {
          'MDO_BINARIES_PATH': binPath,
          'TMPDIR': Directory.systemTemp.path,
        },
        sync: false,
      );

      final portFile =
          File('${Directory.systemTemp.path}/mdo_server_port.txt');
      int? port;
      for (var i = 0; i < 100; i++) {
        await Future.delayed(const Duration(milliseconds: 100));
        if (await portFile.exists()) {
          final content = await portFile.readAsString();
          port = int.tryParse(content.trim());
          if (port != null) break;
        }
      }

      if (port == null) {
        // Debug: Prüfe ob Port-Datei existiert
        final exists = await portFile.exists();
        final tmpDir = Directory.systemTemp.path;
        setState(() {
          _error =
              'Python-Server konnte nicht gestartet werden.\n'
              'Port-Datei: $tmpDir/mdo_server_port.txt (exists: $exists)\n'
              'Binaries: $binPath';
          _loading = false;
        });
        return;
      }

      final engine = MdoEngine(port: port);
      for (var i = 0; i < 20; i++) {
        if (await engine.isHealthy()) break;
        await Future.delayed(const Duration(milliseconds: 100));
      }

      ref.read(engineProvider.notifier).setEngine(engine);
      setState(() => _loading = false);
    } catch (e, stackTrace) {
      setState(() {
        _error = 'Fehler: $e\n\n$stackTrace';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const MaterialApp(
        home: Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    if (_error != null) {
      return MaterialApp(
        home: Scaffold(
          body: Center(child: Text(_error!)),
        ),
      );
    }

    return const MdoApp();
  }
}
