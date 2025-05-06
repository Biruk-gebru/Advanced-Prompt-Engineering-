class Article {
  final String content;
  final String summary;

  Article({
    required this.content,
    required this.summary,
  });

  factory Article.fromJson(Map<String, dynamic> json) {
    return Article(
      content: json['content'] as String,
      summary: json['summary'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'content': content,
      'summary': summary,
    };
  }
} 