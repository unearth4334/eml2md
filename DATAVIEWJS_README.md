# Email Reader - DataviewJS Alternative

This document explains the DataviewJS alternative to the FastAPI GUI for reading email threads in Obsidian.

## Problem

The original GUI uses a FastAPI server on localhost:8000, which may encounter network permission errors in restricted environments:

```
ERROR: [Errno 13] error while attempting to bind on address ('127.0.0.1', 8000): 
an attempt was made to access a socket in a way forbidden by its access permissions
```

## Solution

The DataviewJS implementation provides the same functionality but runs entirely within Obsidian, eliminating network requirements.

## Setup Instructions

1. **Install Obsidian**: Download from https://obsidian.md/
2. **Enable Dataview Plugin**: 
   - Go to Settings → Community Plugins
   - Browse and install "Dataview"
   - Enable the plugin
3. **Copy the GUI file**: Place `email_reader_gui.md` in your Obsidian vault
4. **Open the file**: The GUI will appear automatically when you view the file

## Features

The DataviewJS GUI provides:

- **File Browser**: Select any markdown file in your vault containing email threads
- **Email Parsing**: Automatically parses email metadata and content
- **Preview List**: Shows all emails with truncated previews
- **Individual Extraction**: Select specific emails to extract
- **Obsidian Integration**: 
  - Copy formatted output to clipboard
  - Create new notes directly from extracted emails
  - Full Obsidian YAML frontmatter support

## Comparison with Python Script

| Feature | Python Script | DataviewJS GUI |
|---------|---------------|----------------|
| File Selection | tkinter dialog | Obsidian file browser |
| Email Parsing | ✅ | ✅ |
| Preview Display | Console output | Interactive HTML |
| Email Selection | Console input | Click buttons |
| Output Format | YAML + content | YAML + content |
| Clipboard Copy | ✅ | ✅ |
| New Note Creation | ❌ | ✅ |
| Network Requirements | None | None |
| GUI Requirements | tkinter | Obsidian + Dataview |

## Usage Example

1. Open `email_reader_gui.md` in Obsidian
2. Use the dropdown to select a markdown file (e.g., `sample_email_thread.md`)
3. Click "Load Emails" to parse the file
4. Browse the email list with previews
5. Click "Extract This Email" for any email you want
6. Use "Copy to Clipboard" or "Create New Note" buttons

## File Format Requirements

The DataviewJS GUI expects the same markdown format as the Python script:

```markdown
## Email 1

**Date**: 2024-01-15 09:30:00
**From**: sender@example.com
**To**: recipient@example.com
**Subject**: Subject Line

### Content

Email content here...

---

## Email 2
...
```

## Benefits of DataviewJS Approach

1. **No Network Issues**: Runs entirely within Obsidian
2. **Better Integration**: Creates notes directly in your vault
3. **Visual Interface**: More user-friendly than console
4. **No External Dependencies**: Only requires Obsidian + Dataview
5. **Portable**: Works on any system with Obsidian

This solution maintains all the core functionality while eliminating the network binding issues that prevent the FastAPI server from working in restricted environments.