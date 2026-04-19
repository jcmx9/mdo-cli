import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:mdo_app/screens/home_screen.dart';

final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
  ],
);

class MdoApp extends StatelessWidget {
  const MdoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'mdo',
      theme: ThemeData(
        colorSchemeSeed: Colors.blueGrey,
        useMaterial3: true,
      ),
      routerConfig: router,
    );
  }
}
