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
  final _dateController = TextEditingController();
  String _selectedProfile = 'default';
  bool _signature = true;
  bool _loading = true;
  List<String> _profiles = [];
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
      _profiles = await engine.listProfiles();
      if (_profiles.isNotEmpty) {
        _selectedProfile = _profiles.first;
        _profileData = await engine.loadProfile(_selectedProfile);
        _signature = _profileData['signature'] != false;
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
        if (fm['date'] != null) {
          _dateController.text = fm['date'].toString();
        }
        _signature = fm['signature'] != false && fm['signature'] != null;
      } else {
        _recipientController.text =
            'Firma/Amt\nVorname Nachname\nStrasse 1\n12345 Stadt';
        _bodyController.text = 'Sehr geehrte Damen und Herren,\n\n';
      }
    } catch (_) {}
    setState(() => _loading = false);
  }

  Future<void> _onProfileChanged(String? name) async {
    if (name == null) return;
    final engine = ref.read(engineProvider);
    if (engine == null) return;
    _selectedProfile = name;
    _profileData = await engine.loadProfile(name);
    setState(() {});
  }

  Map<String, dynamic> _buildFrontmatter() {
    final fm = {
      ..._profileData,
      'subject':
          _subjectController.text.isEmpty ? null : _subjectController.text,
      'date':
          _dateController.text.isEmpty ? null : _dateController.text,
      'signature': _signature,
      'recipient': _recipientController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
      'attachments': _attachmentsController.text
          .split('\n')
          .where((l) => l.trim().isNotEmpty)
          .toList(),
    };
    // Empty strings → null for optional fields
    for (final key in ['accent', 'signature_width']) {
      if (fm[key] is String && (fm[key] as String).isEmpty) {
        fm[key] = null;
      }
    }
    return fm;
  }

  Future<void> _save() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    try {
      await engine.saveLetter(
        frontmatter: _buildFrontmatter(),
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

    try {
      final savedPath = await engine.saveLetter(
        frontmatter: _buildFrontmatter(),
        body: _bodyController.text,
        filename: widget.filename,
      );
      final pdfPath = await engine.compile(savedPath);
      ref.invalidate(letterListProvider);
      // PDF im Finder anzeigen
      await Process.run('open', ['-R', pdfPath]);
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
    _dateController.dispose();
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
          // Tab 1: Metadaten
          ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Profil-Auswahl
              if (_profiles.length > 1) ...[
                DropdownButtonFormField<String>(
                  value: _selectedProfile,
                  decoration: const InputDecoration(
                    labelText: 'Profil',
                    border: OutlineInputBorder(),
                  ),
                  items: _profiles
                      .map((p) => DropdownMenuItem(value: p, child: Text(p)))
                      .toList(),
                  onChanged: _onProfileChanged,
                ),
                const SizedBox(height: 12),
              ],
              TextFormField(
                controller: _subjectController,
                decoration: const InputDecoration(
                  labelText: 'Betreff',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _dateController,
                decoration: const InputDecoration(
                  labelText: 'Datum (leer = heute)',
                  hintText: 'z.B. 21. April 2026',
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
              const SizedBox(height: 8),
              SwitchListTile(
                title: const Text('Unterschrift'),
                value: _signature,
                onChanged: (v) => setState(() => _signature = v),
              ),
            ],
          ),
          // Tab 2: Brieftext (Markdown)
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
