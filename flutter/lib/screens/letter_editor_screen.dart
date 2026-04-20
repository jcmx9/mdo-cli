import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/letter_provider.dart';

class LetterEditorScreen extends ConsumerStatefulWidget {
  final String? filename;

  const LetterEditorScreen({super.key, this.filename});

  @override
  ConsumerState<LetterEditorScreen> createState() =>
      _LetterEditorScreenState();
}

class _LetterEditorScreenState extends ConsumerState<LetterEditorScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _subjectController = TextEditingController();
  final _recipientController = TextEditingController();
  final _bodyController = TextEditingController();
  final _attachmentsController = TextEditingController();
  String _selectedProfile = 'default';
  bool _loading = true;
  Map<String, dynamic> _profileData = {};

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  Future<void> _loadData() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    try {
      final profiles = await engine.listProfiles();
      if (profiles.isNotEmpty) {
        _selectedProfile = profiles.first;
        _profileData = await engine.loadProfile(_selectedProfile);
      }

      if (widget.filename != null) {
        final data = await engine.loadLetter(widget.filename!);
        final fm = data['frontmatter'] as Map<String, dynamic>;
        _subjectController.text = fm['subject']?.toString() ?? '';
        final recipients = fm['recipient'] as List? ?? [];
        _recipientController.text = recipients.join('\n');
        _bodyController.text = data['body']?.toString() ?? '';
        final attachments = fm['attachments'] as List? ?? [];
        _attachmentsController.text = attachments.join('\n');
      } else {
        _recipientController.text =
            'Firma/Amt\nVorname Nachname\nStrasse 1\n12345 Stadt';
      }
    } catch (_) {
      // Leere Felder anzeigen
    }
    setState(() => _loading = false);
  }

  Future<void> _save() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    final frontmatter = <String, dynamic>{
      ..._profileData,
      'subject':
          _subjectController.text.isEmpty ? null : _subjectController.text,
      'date': null,
      'recipient': _recipientController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
      'attachments': _attachmentsController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
    };

    try {
      await engine.saveLetter(
        frontmatter: frontmatter,
        body: _bodyController.text,
        filename: widget.filename,
      );
      ref.invalidate(letterListProvider);
      if (mounted) context.pop();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
  }

  Future<void> _compile() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    // Erst speichern
    final frontmatter = <String, dynamic>{
      ..._profileData,
      'subject':
          _subjectController.text.isEmpty ? null : _subjectController.text,
      'date': null,
      'recipient': _recipientController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
      'attachments': _attachmentsController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
    };

    try {
      final savedPath = await engine.saveLetter(
        frontmatter: frontmatter,
        body: _bodyController.text,
        filename: widget.filename,
      );
      // PDF auf den Desktop ausgeben
      final desktop = '${Platform.environment['HOME']}/Desktop';
      final pdfPath = await engine.compile(savedPath, outputDir: desktop);
      ref.invalidate(letterListProvider);
      if (mounted) {
        context.push('/pdf/${Uri.encodeComponent(pdfPath)}');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    _subjectController.dispose();
    _recipientController.dispose();
    _bodyController.dispose();
    _attachmentsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.filename != null;

    if (_loading) {
      return Scaffold(
        appBar: AppBar(
            title: Text(isEdit ? 'Brief bearbeiten' : 'Neuer Brief')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Brief bearbeiten' : 'Neuer Brief'),
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            tooltip: 'Speichern',
            onPressed: _save,
          ),
          IconButton(
            icon: const Icon(Icons.picture_as_pdf),
            tooltip: 'Kompilieren',
            onPressed: _compile,
          ),
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Metadaten'),
            Tab(text: 'Brieftext'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              TextFormField(
                controller: _subjectController,
                decoration: const InputDecoration(
                  labelText: 'Betreff',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _recipientController,
                maxLines: 5,
                decoration: const InputDecoration(
                  labelText: 'Empfänger (eine Zeile pro Adresszeile)',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _attachmentsController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Anlagen (eine pro Zeile, optional)',
                  border: OutlineInputBorder(),
                  alignLabelWithHint: true,
                ),
              ),
            ],
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextFormField(
              controller: _bodyController,
              maxLines: null,
              expands: true,
              textAlignVertical: TextAlignVertical.top,
              style: const TextStyle(fontFamily: 'monospace'),
              decoration: const InputDecoration(
                hintText: 'Sehr geehrte Damen und Herren,\n\n...',
                border: OutlineInputBorder(),
                alignLabelWithHint: true,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
