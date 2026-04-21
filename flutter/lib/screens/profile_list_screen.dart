import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';

class ProfileListScreen extends ConsumerWidget {
  const ProfileListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profilesAsync = ref.watch(profileListProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/profile/create'),
        child: const Icon(Icons.add),
      ),
      body: profilesAsync.when(
        data: (profiles) {
          if (profiles.isEmpty) {
            return const Center(
              child:
                  Text('Keine Profile vorhanden.\nErstelle ein neues Profil.'),
            );
          }
          return ListView.builder(
            itemCount: profiles.length,
            itemBuilder: (context, index) {
              final name = profiles[index];
              return ListTile(
                leading: const Icon(Icons.person),
                title: Text(name),
                trailing: profiles.length > 1
                    ? IconButton(
                        icon: const Icon(Icons.delete),
                        onPressed: () async {
                          final engine = ref.read(engineProvider);
                          if (engine == null) return;
                          try {
                            await engine.call(
                                'delete_profile', {'name': name});
                            ref.invalidate(profileListProvider);
                          } catch (e) {
                            if (context.mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Fehler: $e')),
                              );
                            }
                          }
                        },
                      )
                    : null,
                onTap: () => context.push('/profile/edit/$name'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Fehler: $e')),
      ),
    );
  }
}
