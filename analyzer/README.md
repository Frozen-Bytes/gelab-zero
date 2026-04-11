# Analyzer Module

The Analyzer performs **Reverse Engineering** on Android applications to provide context to the AI.

### Workflow
1. **Extractor**: Coordinates the parsing of manifest, strings, and smali files.
2. **Parser**: Uses Regex and XML parsing to find activities, permissions, and UI labels.
3. **Summarizer**: Condenses technical data into a natural language paragraph for the AI's prompt.
