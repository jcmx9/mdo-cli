import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:mdo_app/engine/mdo_engine.dart';

void main() {
  late HttpServer mockServer;
  late MdoEngine engine;

  setUp(() async {
    mockServer = await HttpServer.bind('127.0.0.1', 0);
    mockServer.listen((request) async {
      if (request.uri.path == '/health') {
        request.response
          ..headers.contentType = ContentType.json
          ..write(jsonEncode({'status': 'ok'}))
          ..close();
        return;
      }
      if (request.uri.path == '/rpc' && request.method == 'POST') {
        final body = await utf8.decoder.bind(request).join();
        final data = jsonDecode(body) as Map<String, dynamic>;
        final method = data['method'] as String;

        Map<String, dynamic> response;
        if (method == 'list_profiles') {
          response = {
            'result': ['default', 'work']
          };
        } else if (method == 'load_profile') {
          response = {
            'result': {
              'name': 'Test User',
              'street': 'Teststr 1',
              'zip': '12345',
              'city': 'Teststadt',
            }
          };
        } else if (method == 'get_template_version') {
          response = {'result': '0.2.0'};
        } else {
          response = {'error': 'Unknown method: $method'};
        }

        request.response
          ..headers.contentType = ContentType.json
          ..write(jsonEncode(response))
          ..close();
        return;
      }
      request.response
        ..statusCode = 404
        ..close();
    });

    engine = MdoEngine(port: mockServer.port);
  });

  tearDown(() async {
    engine.dispose();
    await mockServer.close();
  });

  test('health check returns true', () async {
    final healthy = await engine.isHealthy();
    expect(healthy, isTrue);
  });

  test('listProfiles returns profile names', () async {
    final profiles = await engine.listProfiles();
    expect(profiles, equals(['default', 'work']));
  });

  test('loadProfile returns profile data', () async {
    final profile = await engine.loadProfile('default');
    expect(profile['name'], equals('Test User'));
    expect(profile['city'], equals('Teststadt'));
  });

  test('getTemplateVersion returns version string', () async {
    final version = await engine.getTemplateVersion();
    expect(version, equals('0.2.0'));
  });

  test('call with unknown method throws exception', () async {
    expect(
      () => engine.call('nonexistent', {}),
      throwsException,
    );
  });
}
