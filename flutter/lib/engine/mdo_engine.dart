import 'dart:convert';
import 'package:http/http.dart' as http;

/// HTTP-Client zum lokalen Python-Backend.
class MdoEngine {
  final int port;
  final http.Client _client;

  MdoEngine({required this.port, http.Client? client})
      : _client = client ?? http.Client();

  String get _baseUrl => 'http://127.0.0.1:$port';

  /// Prüft ob der Server erreichbar ist.
  Future<bool> isHealthy() async {
    try {
      final response = await _client.get(Uri.parse('$_baseUrl/health'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return data['status'] == 'ok';
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Sendet einen JSON-RPC-Aufruf an den Server.
  Future<dynamic> call(String method, Map<String, dynamic> params) async {
    final response = await _client.post(
      Uri.parse('$_baseUrl/rpc'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'method': method, 'params': params}),
    );

    final data = jsonDecode(response.body) as Map<String, dynamic>;

    if (data.containsKey('error')) {
      throw Exception(data['error']);
    }

    return data['result'];
  }

  /// Gibt alle Profilnamen zurück.
  Future<List<String>> listProfiles() async {
    final result = await call('list_profiles', {});
    return (result as List).cast<String>();
  }

  /// Lädt ein Profil als Map.
  Future<Map<String, dynamic>> loadProfile(String name) async {
    final result = await call('load_profile', {'name': name});
    return result as Map<String, dynamic>;
  }

  /// Gibt die installierte Template-Version zurück.
  Future<String?> getTemplateVersion() async {
    final result = await call('get_template_version', {});
    return result as String?;
  }

  /// Kompiliert eine .md-Datei zu PDF.
  Future<String> compile(String path, {String? outputDir}) async {
    final result = await call('compile', {
      'path': path,
      if (outputDir != null) 'output_dir': outputDir,
    });
    return (result as Map<String, dynamic>)['pdf_path'] as String;
  }

  /// Kopiert eine Signatur-Datei nach ~/.mdo/unterschrift_PROFILNAME.ext.
  Future<String> copySignature(String sourcePath, String profileName) async {
    final result = await call('copy_signature', {
      'source': sourcePath,
      'profile_name': profileName,
    });
    return result as String;
  }

  /// Speichert einen Brief.
  Future<String> saveLetter({
    required Map<String, dynamic> frontmatter,
    required String body,
    String? filename,
  }) async {
    final result = await call('save_letter', {
      'frontmatter': frontmatter,
      'body': body,
      if (filename != null) 'filename': filename,
    });
    return result as String;
  }

  /// Lädt einen Brief.
  Future<Map<String, dynamic>> loadLetter(String filename) async {
    final result = await call('load_letter', {'filename': filename});
    return result as Map<String, dynamic>;
  }

  /// Listet alle Briefe auf.
  Future<List<String>> listLetters() async {
    final result = await call('list_letters', {});
    return (result as List).cast<String>();
  }

  /// Löscht einen Brief.
  Future<void> deleteLetter(String filename) async {
    await call('delete_letter', {'filename': filename});
  }

  /// Prüft den Font-Status.
  Future<Map<String, dynamic>> checkFonts() async {
    final result = await call('check_fonts', {});
    return result as Map<String, dynamic>;
  }

  /// Installiert fehlende Fonts.
  Future<void> installFonts() async {
    await call('install_fonts', {});
  }

  /// Aktualisiert das Typst-Template.
  Future<String> installTemplate() async {
    final result = await call('install_template', {});
    return result as String;
  }

  void dispose() {
    _client.close();
  }
}
