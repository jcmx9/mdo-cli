import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final engine = ref.watch(engineProvider);
    final profilesAsync = ref.watch(profileListProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('mdo'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Icon(
              engine != null ? Icons.check_circle : Icons.error,
              color: engine != null ? Colors.green : Colors.red,
            ),
          ),
        ],
      ),
      body: Center(
        child: profilesAsync.when(
          data: (profiles) {
            if (profiles.isEmpty) {
              return const Text('Keine Profile gefunden.');
            }
            return ListView.builder(
              itemCount: profiles.length,
              itemBuilder: (context, index) => ListTile(
                leading: const Icon(Icons.person),
                title: Text(profiles[index]),
              ),
            );
          },
          loading: () => const CircularProgressIndicator(),
          error: (error, _) => Text('Fehler: $error'),
        ),
      ),
    );
  }
}
