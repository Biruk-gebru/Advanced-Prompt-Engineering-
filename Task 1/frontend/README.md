# Frontend Implementation

This directory contains the Flutter frontend implementation for the Research Article Tailoring System.

## Setup

1. Install Flutter dependencies:
```bash
flutter pub get
```

2. Configure backend URL:
- Update the API endpoint in `lib/services/api_service.dart`
- Default is `http://localhost:8000`

## Running the Application

```bash
# For web
flutter run -d chrome

# For desktop
flutter run

# For specific device
flutter devices  # List available devices
flutter run -d device_id
```

## Features

1. User Interface:
   - Clean, modern Material Design
   - Responsive layout
   - Cross-platform support

2. Input Methods:
   - Direct topic input
   - PDF file upload (with size validation)
   - Paper URL input (currently disabled)

3. Educational Levels:
   - Middle School
   - High School
   - Undergraduate
   - Graduate
   - PhD

4. Output Display:
   - Markdown rendering
   - Article summary view
   - Full article view
   - Copy to clipboard
   - Download options

## Known Issues

1. File Upload:
   - Size limitations (10MB max)
   - Token limit constraints
   - PDF processing dependencies

2. URL Processing:
   - Currently not functional
   - Planned for future implementation

## Testing

```bash
flutter test
```

## Building for Production

```bash
# Web
flutter build web

# Windows
flutter build windows

# macOS
flutter build macos

# Linux
flutter build linux
``` 