# Research Article Tailoring System - Task 1

This directory contains the implementation of an AI-powered research article tailoring system that adapts complex content for different educational levels using GitHub's AI model.

## Directory Structure

```
Task 1/
├── backend/         # FastAPI backend implementation
├── frontend/        # Flutter frontend implementation
└── docs/           # Documentation and system design
```

## Current Implementation Status

### Working Features
- Direct topic input with educational level adaptation
- Markdown-formatted output
- Advanced prompt engineering techniques:
  - Chain of Thought reasoning
  - Few-shot learning

### Known Limitations
- Research paper URL processing is not functional
- File uploads may fail due to token limitations in the GitHub AI model
- Large PDF files (>10MB) are not supported
- Poppler installation is required for PDF processing

## Setup Instructions

Please refer to the individual README files in the backend and frontend directories for specific setup instructions.

### Quick Start

1. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `.\venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. Configure environment:
- Create a `.env` file in the backend directory
- Add your GitHub token: `GITHUB_TOKEN=your_token_here`

3. Set up the frontend:
```bash
cd frontend
flutter pub get
```

4. Run the application:
- Backend: `uvicorn main:app --reload`
- Frontend: `flutter run`

## Documentation

Detailed documentation including system design, API specifications, and implementation details can be found in the `docs` directory. 