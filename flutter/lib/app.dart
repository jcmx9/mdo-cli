import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/screens/letter_editor_screen.dart';
import 'package:mdo_app/screens/letter_list_screen.dart';
import 'package:mdo_app/screens/pdf_preview_screen.dart';
import 'package:mdo_app/screens/profile_form_screen.dart';
import 'package:mdo_app/screens/profile_list_screen.dart';
import 'package:mdo_app/screens/settings_screen.dart';

final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const LetterListScreen(),
    ),
    GoRoute(
      path: '/profiles',
      builder: (context, state) => const ProfileListScreen(),
    ),
    GoRoute(
      path: '/profile/create',
      builder: (context, state) => const ProfileFormScreen(),
    ),
    GoRoute(
      path: '/profile/edit/:name',
      builder: (context, state) => ProfileFormScreen(
        profileName: state.pathParameters['name'],
      ),
    ),
    GoRoute(
      path: '/letter/new',
      builder: (context, state) => const LetterEditorScreen(),
    ),
    GoRoute(
      path: '/letter/edit/:filename',
      builder: (context, state) => LetterEditorScreen(
        filename: state.pathParameters['filename'],
      ),
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
    GoRoute(
      path: '/pdf/:path',
      builder: (context, state) => PdfPreviewScreen(
        pdfPath: Uri.decodeComponent(state.pathParameters['path'] ?? ''),
      ),
    ),
  ],
);

class MdoApp extends StatelessWidget {
  const MdoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'MarkdownOffice',
      theme: ThemeData(
        colorSchemeSeed: Colors.blueGrey,
        useMaterial3: true,
      ),
      routerConfig: router,
    );
  }
}
