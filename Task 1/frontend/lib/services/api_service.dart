import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';
import '../models/article.dart';
import 'dart:typed_data';

class ApiService {
  static const String baseUrl = 'http://localhost:8000';

  Future<Article> generateArticle({
    String? topic,
    required String audienceLevel,
    String? paperUrl,
    Uint8List? pdfFile,
  }) async {
    try {
      var uri = Uri.parse('$baseUrl/generate_article');
      var request = http.MultipartRequest('POST', uri);

      // Create the request body
      var requestData = {
        if (topic != null && topic.isNotEmpty) 'topic': topic,
        'audience_level': audienceLevel,
        if (paperUrl != null && paperUrl.isNotEmpty) 'paper_url': paperUrl,
      };

      // Add the request data as a field
      request.fields['request'] = jsonEncode(requestData);

      // Add PDF file if provided
      if (pdfFile != null) {
        request.files.add(
          http.MultipartFile.fromBytes(
            'file',
            pdfFile,
            filename: 'paper.pdf',
            contentType: MediaType('application', 'pdf'),
          ),
        );
      }

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return Article.fromJson(jsonDecode(response.body));
      } else {
        // Try to parse error message from response
        try {
          final errorData = jsonDecode(response.body);
          throw Exception(errorData['detail'] ?? 'Failed to generate article');
        } catch (e) {
          if (e is Exception) rethrow;
          throw Exception('Failed to generate article: ${response.body}');
        }
      }
    } catch (e) {
      if (e is Exception) rethrow;
      throw Exception('Error generating article: $e');
    }
  }
} 