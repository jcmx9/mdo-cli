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
  final _controllers = <String, TextEditingController>{};
  bool _qrCode = false;
  bool _signature = true;
  bool _loading = true;
  bool _saving = false;

  static const _fields = [
    ('name', 'Name'),
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

  @override
  void initState() {
    super.initState();
    for (final (key, _) in _fields) {
      _controllers[key] = TextEditingController();
    }
    _controllers['closing']!.text = 'Mit freundlichem Gruß';
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    if (widget.profileName == null) {
      setState(() => _loading = false);
      return;
    }
    final engine = ref.read(engineProvider);
    if (engine == null) return;
    try {
      final data = await engine.loadProfile(widget.profileName!);
      for (final (key, _) in _fields) {
        final value = data[key];
        if (value != null) _controllers[key]!.text = value.toString();
      }
      setState(() {
        _qrCode = data['qr_code'] == true;
        _signature = data['signature'] != false;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
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

    try {
      final name = widget.profileName ?? 'default';
      await engine.call('save_profile', {'name': name, 'data': data});
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
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.profileName != null;

    if (_loading) {
      return Scaffold(
        appBar: AppBar(
            title: Text(isEdit ? 'Profil bearbeiten' : 'Neues Profil')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(isEdit ? 'Profil bearbeiten' : 'Neues Profil'),
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
          ],
        ),
      ),
    );
  }
}
