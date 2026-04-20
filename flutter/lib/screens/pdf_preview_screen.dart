import 'package:flutter/material.dart';
import 'package:pdfrx/pdfrx.dart';

class PdfPreviewScreen extends StatelessWidget {
  final String pdfPath;

  const PdfPreviewScreen({super.key, required this.pdfPath});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('PDF-Vorschau'),
      ),
      body: PdfViewer.file(pdfPath),
    );
  }
}
