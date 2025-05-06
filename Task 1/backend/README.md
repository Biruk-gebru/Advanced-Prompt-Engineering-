# Backend Implementation

This directory contains the FastAPI backend implementation for the Research Article Tailoring System.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
Create a `.env` file in this directory with the following content:
```
GITHUB_TOKEN=your_github_token_here
```

4. Install Poppler (required for PDF processing):
- Windows: Download from http://blog.alivate.com.au/poppler-windows/
- MacOS: `brew install poppler`
- Linux: `sudo apt-get install poppler-utils`

## Running the Server

```bash
uvicorn main:app --reload
```

## API Endpoints

### POST /generate_article
Generates an article based on input type and educational level.

Request body:
```json
{
    "input_type": "topic",  // or "pdf" or "url"
    "content": "string",    // topic, PDF content, or URL
    "level": "string"       // educational level
}
```

Response:
```json
{
    "article": "string",    // generated article
    "summary": "string"     // article summary
}
```

## Known Issues

1. Token Errors:
   - Check GITHUB_TOKEN in .env
   - Verify token permissions
   - Monitor API rate limits

2. PDF Processing:
   - Ensure Poppler is installed correctly
   - Check file size limits (max 10MB)
   - Verify PDF format

3. URL Processing:
   - Currently not functional
   - Planned for future implementation 