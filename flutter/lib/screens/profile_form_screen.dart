import 'package:desktop_drop/desktop_drop.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/providers/engine_provider.dart';
import 'package:mdo_app/providers/profile_provider.dart';

class ProfileFormScreen extends ConsumerStatefulWidget {
  final String? profileName;

  const ProfileFormScreen({super.key, this.profileName});

  @override
  ConsumerState<ProfileFormScreen> createState() => _ProfileFormScreenState();
}

class _ProfileFormScreenState extends ConsumerState<ProfileFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _profileNameController = TextEditingController();
  final _controllers = <String, TextEditingController>{};
  bool _qrCode = false;
  bool _signature = true;
  bool _loading = true;
  bool _saving = false;
  bool _dragging = false;
  String? _signaturePath;
  List<String> _existingProfiles = [];

  static const _fields = [
    ('name', 'Absendername'),
    ('street', 'Strasse'),
    ('zip', 'PLZ'),
    ('city', 'Ort'),
    ('phone', 'Telefon'),
    ('email', 'E-Mail'),
    ('iban', 'IBAN'),
    ('bic', 'BIC'),
    ('bank', 'Bank'),
    ('accent', 'Akzentfarbe (Hex)'),
    ('closing', 'Schlussgruss'),
  ];

  bool get _isEdit => widget.profileName != null;

  @override
  void initState() {
    super.initState();
    for (final (key, _) in _fields) {
      _controllers[key] = TextEditingController();
    }
    _controllers['closing']!.text = 'Mit freundlichem Gruß';
    if (_isEdit) {
      _profileNameController.text = widget.profileName!;
    }
    _loadData();
  }

  Future<void> _loadData() async {
    final engine = ref.read(engineProvider);
    if (engine == null) return;

    try {
      _existingProfiles = await engine.listProfiles();

      if (_isEdit) {
        final data = await engine.loadProfile(widget.profileName!);
        for (final (key, _) in _fields) {
          final value = data[key];
          if (value != null) _controllers[key]!.text = value.toString();
        }
        _qrCode = data['qr_code'] == true;
        _signature = data['signature'] != false;

        // Unterschrift-Pfad laden
        final sig = await engine.findSignature(widget.profileName!);
        if (sig != null) _signaturePath = sig;
      }
    } catch (_) {}
    setState(() => _loading = false);
  }

  String? _validateProfileName(String? value) {
    if (value == null || value.trim().isEmpty) return 'Pflichtfeld';
    final name = value.trim().toLowerCase();
    if (RegExp(r'[^a-z0-9_-]').hasMatch(name)) {
      return 'Nur Kleinbuchstaben, Zahlen, - und _';
    }
    // Doppelte Namen verhindern (außer beim Bearbeiten des eigenen Namens)
    if (!_isEdit || value.trim() != widget.profileName) {
      if (_existingProfiles.contains(value.trim())) {
        return 'Profil "$value" existiert bereits';
      }
    }
    return null;
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    final engine = ref.read(engineProvider);
    if (engine == null) return;

    final data = <String, dynamic>{};
    for (final (key, _) in _fields) {
      final text = _controllers[key]!.text;
      if (key == 'accent' && text.isEmpty) {
        data[key] = null;
      } else {
        data[key] = text;
      }
    }
    data['qr_code'] = _qrCode;
    data['signature'] = _signature;
    data['open'] = true;
    data['reveal'] = true;

    final newName = _profileNameController.text.trim();

    try {
      // Speichern unter neuem Namen
      await engine.call('save_profile', {'name': newName, 'data': data});

      // Bei Umbenennung: altes Profil löschen
      if (_isEdit && widget.profileName != newName) {
        try {
          await engine.call(
              'delete_profile', {'name': widget.profileName});
        } catch (_) {
          // Altes Profil konnte nicht gelöscht werden — nicht schlimm
        }
      }

      ref.invalidate(profileListProvider);
      if (mounted) {
        context.pop();
        return;
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fehler: $e')),
        );
      }
    }
    if (mounted) setState(() => _saving = false);
  }

  @override
  void dispose() {
    _profileNameController.dispose();
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(
            title: Text(_isEdit ? 'Profil bearbeiten' : 'Neues Profil')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_isEdit ? 'Profil bearbeiten' : 'Neues Profil'),
        actions: [
          if (_saving)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2)),
            )
          else
            IconButton(onPressed: _save, icon: const Icon(Icons.save)),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Profilname (Verzeichnisname)
            TextFormField(
              controller: _profileNameController,
              decoration: const InputDecoration(
                labelText: 'Profilname',
                hintText: 'z.B. privat, geschaeftlich',
                border: OutlineInputBorder(),
                helperText: 'Interner Name (Kleinbuchstaben, keine Leerzeichen)',
              ),
              validator: _validateProfileName,
            ),
            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),

            // Absenderdaten
            for (final (key, label) in _fields)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: TextFormField(
                  controller: _controllers[key],
                  decoration: InputDecoration(
                    labelText: label,
                    border: const OutlineInputBorder(),
                  ),
                  validator: (key == 'name' ||
                          key == 'street' ||
                          key == 'zip' ||
                          key == 'city')
                      ? (v) => (v == null || v.isEmpty) ? 'Pflichtfeld' : null
                      : null,
                ),
              ),
            SwitchListTile(
              title: const Text('vCard QR-Code'),
              value: _qrCode,
              onChanged: (v) => setState(() => _qrCode = v),
            ),
            SwitchListTile(
              title: const Text('Unterschrift'),
              value: _signature,
              onChanged: (v) => setState(() => _signature = v),
            ),
            if (_signature) ...[
              const SizedBox(height: 12),
              DropTarget(
                onDragEntered: (_) => setState(() => _dragging = true),
                onDragExited: (_) => setState(() => _dragging = false),
                onDragDone: (details) async {
                  setState(() => _dragging = false);
                  if (details.files.isEmpty) return;
                  final file = details.files.first;
                  final ext = file.path.split('.').last.toLowerCase();
                  if (!['svg', 'png', 'jpg', 'gif'].contains(ext)) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                            content: Text('Nur SVG, PNG, JPG oder GIF')),
                      );
                    }
                    return;
                  }
                  final engine = ref.read(engineProvider);
                  if (engine == null) return;
                  try {
                    final name = _profileNameController.text.trim().isEmpty
                        ? 'default'
                        : _profileNameController.text.trim();
                    final path =
                        await engine.saveSignature(file.path, name);
                    setState(() => _signaturePath = path);
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Fehler: $e')),
                      );
                    }
                  }
                },
                child: Container(
                  height: 80,
                  decoration: BoxDecoration(
                    border: Border.all(
                      color: _dragging
                          ? Theme.of(context).colorScheme.primary
                          : Colors.grey,
                      width: _dragging ? 2 : 1,
                    ),
                    borderRadius: BorderRadius.circular(8),
                    color: _dragging
                        ? Theme.of(context)
                            .colorScheme
                            .primary
                            .withValues(alpha: 0.1)
                        : Colors.grey.withValues(alpha: 0.05),
                  ),
                  child: Center(
                    child: _signaturePath != null
                        ? Text(
                            'Unterschrift: ${_signaturePath!.split('/').last}',
                            style: const TextStyle(color: Colors.green),
                          )
                        : const Text(
                            'Unterschrift-Datei hierher ziehen\n(SVG, PNG, JPG, GIF)',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.grey),
                          ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
