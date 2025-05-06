import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:file_picker/file_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import 'services/api_service.dart';
import 'models/article.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Research Article Generator',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _formKey = GlobalKey<FormState>();
  final _apiService = ApiService();
  final _topicController = TextEditingController();
  final _urlController = TextEditingController();
  
  String _selectedLevel = 'Undergraduate';
  bool _isLoading = false;
  Article? _article;
  String? _error;
  PlatformFile? _selectedFile;

  final List<String> _audienceLevels = [
    'Middle School',
    'High School',
    'Undergraduate',
    'Graduate',
    'PhD'
  ];

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
    );

    if (result != null) {
      setState(() {
        _selectedFile = result.files.first;
      });
    }
  }

  Future<void> _generateArticle() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _error = null;
      _article = null;
    });

    try {
      final article = await _apiService.generateArticle(
        topic: _topicController.text.isNotEmpty ? _topicController.text : null,
        audienceLevel: _selectedLevel,
        paperUrl: _urlController.text.isNotEmpty ? _urlController.text : null,
        pdfFile: _selectedFile?.bytes,
      );

      setState(() {
        _article = article;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Research Article Generator'),
        elevation: 2,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  TextFormField(
                    controller: _topicController,
                    decoration: const InputDecoration(
                      labelText: 'Research Topic (Optional)',
                      hintText: 'Enter a topic (e.g., Quantum Entanglement)',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _urlController,
                    decoration: const InputDecoration(
                      labelText: 'Paper URL (Optional)',
                      hintText: 'Enter URL to a PDF paper',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _pickFile,
                    icon: const Icon(Icons.upload_file),
                    label: Text(_selectedFile != null 
                      ? 'Selected: ${_selectedFile!.name}'
                      : 'Upload PDF File'),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: _selectedLevel,
                    decoration: const InputDecoration(
                      labelText: 'Audience Level',
                      border: OutlineInputBorder(),
                    ),
                    items: _audienceLevels.map((String level) {
                      return DropdownMenuItem(
                        value: level,
                        child: Text(level),
                      );
                    }).toList(),
                    onChanged: (String? newValue) {
                      if (newValue != null) {
                        setState(() {
                          _selectedLevel = newValue;
                        });
                      }
                    },
                    validator: (value) {
                      if (_topicController.text.isEmpty && 
                          _urlController.text.isEmpty && 
                          _selectedFile == null) {
                        return 'Please provide either a topic, URL, or upload a file';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _generateArticle,
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: _isLoading
                          ? const CircularProgressIndicator()
                          : const Text('Generate Article'),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            if (_error != null)
              Card(
                color: Colors.red[100],
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.red),
                  ),
                ),
              ),
            if (_article != null) ...[
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Summary',
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 8),
                        Text(_article!.summary),
                        const Divider(height: 32),
                        Expanded(
                          child: Markdown(
                            data: _article!.content,
                            selectable: true,
                            onTapLink: (text, href, title) {
                              if (href != null) {
                                launchUrl(Uri.parse(href));
                              }
                            },
                          ),
                        ),
                      ],
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

  @override
  void dispose() {
    _topicController.dispose();
    _urlController.dispose();
    super.dispose();
  }
}
