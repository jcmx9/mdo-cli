import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/letter_provider.dart';

class LetterListScreen extends ConsumerWidget {
  const LetterListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final engine = ref.watch(engineProvider);
    final lettersAsync = ref.watch(letterListProvider);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            SvgPicture.asset('assets/logo.svg', height: 32),
            const SizedBox(width: 8),
            const Text('MarkdownOffice'),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.person),
            tooltip: 'Profile',
            onPressed: () => context.push('/profiles'),
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            tooltip: 'Einstellungen',
            onPressed: () => context.push('/settings'),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.push('/letter/new'),
        child: const Icon(Icons.add),
      ),
      body: lettersAsync.when(
        data: (letters) {
          if (letters.isEmpty) {
            return const Center(
              child: Text(
                  'Keine Briefe vorhanden.\nErstelle einen neuen Brief.'),
            );
          }
          return ListView.builder(
            itemCount: letters.length,
            itemBuilder: (context, index) {
              final filename = letters[index];
              return ListTile(
                leading: const Icon(Icons.mail),
                title: Text(filename),
                trailing: IconButton(
                  icon: const Icon(Icons.delete),
                  onPressed: () async {
                    if (engine == null) return;
                    try {
                      await engine.deleteLetter(filename);
                      ref.invalidate(letterListProvider);
                    } catch (e) {
                      if (context.mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text('Fehler: $e')),
                        );
                      }
                    }
                  },
                ),
                onTap: () => context.push('/letter/edit/$filename'),
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
