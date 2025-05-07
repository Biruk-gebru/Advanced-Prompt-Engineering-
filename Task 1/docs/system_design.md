# System Design Documentation

## Flowchart
```mermaid
graph TD
    A[User Input] --> B{Input Type}
    B -->|Topic| C[Topic Processing]
    B -->|PDF File| D[PDF Processing]
    B -->|Paper URL| E[URL Processing]
    
    D --> F[Extract Text & Images]
    E --> D
    
    C --> G[Prompt Engineering Pipeline]
    F --> G
    
   
    subgraph PE [Prompt Engineering]
        direction TB
        G
        click G "javascript:void(0);"  %% optional, to make clickable if embedded
    end
    
    
    G -->|1. Chain of Thought| H[Core Concept Identification]
    H --> I[Subtopic Breakdown]
    I --> J[Logical Flow Organization]
    
    
    G -->|2. Few-shot Learning| K[Example-based Adaptation]
    K --> L[Audience Level Matching]
    
    
    J --> M[Content Generation]
    L --> M
    
    M --> N[Final Article]
    N --> O[Summary Extraction]
    
    O --> P[Response to User]
```

## Implementation Details

### 1. Input Processing
- Topic-based generation
- PDF file upload with text and image extraction
- URL-based PDF fetching and processing

### 2. Prompt Engineering Techniques

#### Chain of Thought (CoT)
```python
def create_prompt(topic: str, audience_level: str):
    """
    Implements Chain of Thought by breaking down the process:
    1. Core concept identification
    2. Subtopic breakdown
    3. Logical flow organization
    4. Content generation
    """
```

#### Few-shot Learning
```python
def get_few_shot_examples(audience_level: str):
    """
    Provides concrete examples of content adapted for different levels:
    - Middle School (simple, visual)
    - High School (basic technical)
    - Undergraduate (academic)
    - Graduate (advanced)
    - PhD (research-level)
    """
```

### 3. Edge Cases Handling
- Empty or corrupted PDFs
- Network failures in URL fetching
- Invalid file types
- Text extraction failures
- Image processing errors
- Token limit management
- Error reporting and recovery

### 4. External Tools & APIs
1. GitHub AI Model API
   - Used for text generation
   - Handles complex prompts
2. PyPDF2
   - PDF text extraction
3. pdf2image & pytesseract
   - Image extraction and OCR
4. FastAPI
   - Backend API framework
5. Flutter
   - Cross-platform frontend

## Testing & Evaluation

### Test Cases
1. Topic-based generation
   - Simple topics
   - Complex scientific topics
   - Edge cases (very short/long topics)

2. PDF Processing
   - Research papers
   - Text-heavy documents
   - Image-heavy documents
   - Malformed PDFs

3. Audience Levels
   - Content adaptation verification
   - Terminology appropriateness
   - Explanation clarity

### Performance Analysis

#### Strengths
1. Robust input handling (multiple input types)
2. Sophisticated prompt engineering
3. Comprehensive error handling
4. Modern, responsive UI
5. Cross-platform support

#### Limitations
1. PDF processing dependencies
2. API rate limits
3. Long processing times for complex documents
4. OCR accuracy limitations
5. Token limit constraints

## Future Improvements
1. Caching mechanism for processed documents
2. Batch processing capabilities
3. Enhanced error recovery
4. More sophisticated image analysis
5. Additional prompt engineering techniques 
