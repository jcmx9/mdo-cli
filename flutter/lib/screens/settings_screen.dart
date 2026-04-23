import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';
import 'package:mdo_app/providers/settings_provider.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final templateAsync = ref.watch(templateVersionProvider);
    final fontsAsync = ref.watch(fontStatusProvider);
    final profilesAsync = ref.watch(profileListProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SvgPicture.asset('assets/logo.svg', height: 32),
            const SizedBox(width: 8),
            const Text('Einstellungen'),
          ],
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Template
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Typst-Template',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  templateAsync.when(
                    data: (version) => Text(
                        'Version: ${version ?? "nicht installiert"}'),
                    loading: () => const Text('Lade...'),
                    error: (e, _) => Text('Fehler: $e'),
                  ),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(
                    onPressed: () => _updateTemplate(context, ref),
                    icon: const Icon(Icons.download),
                    label: const Text('Template aktualisieren'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Fonts
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Schriftarten',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  fontsAsync.when(
                    data: (status) {
                      final installed = status['installed'] == true;
                      final missing =
                          (status['missing'] as List?)?.cast<String>() ?? [];
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                installed
                                    ? Icons.check_circle
                                    : Icons.warning,
                                color: installed
                                    ? Colors.green
                                    : Colors.orange,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(installed
                                    ? 'Alle Schriftarten installiert'
                                    : 'Fehlend: ${missing.join(", ")}'),
                              ),
                            ],
                          ),
                          if (!installed) ...[
                            const SizedBox(height: 8),
                            ElevatedButton.icon(
                              onPressed: () =>
                                  _installFonts(context, ref),
                              icon: const Icon(Icons.download),
                              label:
                                  const Text('Schriftarten installieren'),
                            ),
                          ],
                        ],
                      );
                    },
                    loading: () => const Text('Lade...'),
                    error: (e, _) => Text('Fehler: $e'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),

          // Profile
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Profile',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  profilesAsync.when(
                    data: (profiles) => Text(
                        '${profiles.length} Profil${profiles.length == 1 ? "" : "e"} vorhanden'),
                    loading: () => const Text('Lade...'),
                    error: (e, _) => Text('Fehler: $e'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _updateTemplate(
      BuildContext context, WidgetRef ref) async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Template wird aktualisiert...')),
    );

    try {
      final path = await engine.installTemplate();
      ref.invalidate(templateVersionProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Template installiert: $path')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
  }

  Future<void> _installFonts(
      BuildContext context, WidgetRef ref) async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
          content: Text('Schriftarten werden installiert...')),
    );

    try {
      await engine.installFonts();
      ref.invalidate(fontStatusProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Schriftarten installiert')),
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
  }
}
