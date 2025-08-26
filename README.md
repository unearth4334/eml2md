# EML to Markdown Converter

This tool converts email files (`.eml`) to Markdown format (`.md`) while preserving the email thread structure, extracting attachments, and intelligently removing duplicate emails in threads.

## Features

- Converts `.eml` files to Markdown format
- Preserves email thread structure using multiple methods:
  - Standard RFC822 embedded message detection
  - Pattern matching to detect quoted emails in the body text
  - SimHash-based deduplication to remove redundant email content
- Extracts and saves attachments
- Organizes content in chronological order (oldest-to-newest or newest-to-oldest)
- Moves processed files to a separate directory
- Creates a clean directory structure for output files

## Directory Structure

```
project/
├── input/         # Place .eml files here
├── output/        # Converted files will be saved here (one directory per email)
│   └── email1/    # Example output directory
│       ├── email1.md
│       └── [attachments]
├── done/          # Processed .eml files are moved here
├── .gitignore     # Configured to ignore email content
└── create_gitkeep.py  # Utility script to set up directory structure
```

## Installation

1. Make sure you have Python 3.7+ installed
2. Clone this repository or download the source code
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the required directory structure:

```bash
python create_gitkeep.py
```

## Usage

### Command Line Interface

1. Place your `.eml` files in the `input` directory
2. Run the script:

```bash
# Default: oldest to newest email order, default deduplication
python eml2md.py

# Optional: newest to oldest email order
python eml2md.py --newest-first

# Adjust deduplication sensitivity (higher = more aggressive)
python eml2md.py --dedup-threshold 12
```

3. Find your converted files in the `output` directory, organized in subdirectories named after the original email files

### Graphical User Interface

Launch the FastAPI-based GUI for a web interface:

```bash
# Start the GUI application
python run_gui.py

# For debugging server startup issues, use verbose mode
python run_gui.py --verbose
```

This will:
- Start a FastAPI web server
- Open a chromium-based browser window with the interface
- Automatically terminate the server when the window is closed

If the GUI fails to start, use the `--verbose` flag to see detailed error messages that will help identify the problem (e.g., port conflicts, missing dependencies, browser issues).

![FastAPI GUI Interface](https://github.com/user-attachments/assets/a5231a9a-31d8-475b-ab31-1f8b9beac84a)

### Command Line Options

| Option | Description |
|--------|-------------|
| `--newest-first` | Sort emails from newest to oldest in the markdown file (default is oldest to newest) |
| `--dedup-threshold VALUE` | Set the similarity threshold for deduplication (default is 8, higher values mean more aggressive deduplication) |

## Thread Detection and Deduplication

The tool uses three complementary methods to handle email threads:

1. **Embedded Messages**: Detects properly formatted `message/rfc822` parts in multipart emails.

2. **Pattern Matching**: Analyzes the email body text to find patterns indicating quoted emails such as:
   - Outlook format: "From: ... Sent: ... To: ... Subject: ..."
   - Reply format: "On [date], [person] wrote:"
   - Gmail format: "On [date] at [time], [person] wrote:"

3. **SimHash Deduplication**: Uses content-based hashing to identify and remove duplicate emails, even when formatting differs:
   - Creates a fingerprint for each email that preserves similarity
   - Compares emails using Hamming distance between fingerprints
   - Removes duplicates while prioritizing newer emails

### How SimHash Deduplication Works

The SimHash algorithm:
1. Extracts features from the email (sender, subject, key content lines)
2. Creates a 64-bit fingerprint that preserves content similarity
3. Compares fingerprints using Hamming distance (bit differences)
4. Groups similar emails and keeps only the most representative one

The default threshold of 8 bits (out of 64) works well for most emails, but you can adjust it with the `--dedup-threshold` parameter. Higher values will be more aggressive in identifying duplicates.

## Output Format

The generated Markdown file includes:

- Email thread organized chronologically
- Metadata for each email (date, from, to, cc, subject)
- Email content
- Links to extracted attachments

## Example

```markdown
# Email Thread

## Email 1

**Date**: 2023-01-15 14:32:45

**From**: sender@example.com

**To**: recipient@example.com

**Subject**: Example Subject

### Content

This is the content of the email.

### Attachments

- [document.pdf](document.pdf)

---

## Email 2

...
```

## Requirements

- Python 3.7+
- email-validator
- python-dateutil
- fastapi (for GUI)
- uvicorn (for GUI)
- jinja2 (for GUI)  
- psutil (for GUI)
- A chromium-based browser (Google Chrome, Chromium, etc.) for GUI

## Project Components

### Main Script

- `eml2md.py` - The main script that handles the conversion process

### GUI Application

- `app.py` - FastAPI web application providing the GUI interface
- `gui_launcher.py` - Launcher script that starts the server and opens browser window
- `run_gui.py` - Simple entry point for launching the GUI
- `templates/` - HTML templates for the web interface

### Utility Scripts

- `create_gitkeep.py` - Sets up the required directory structure and creates .gitkeep files to ensure the directories are tracked by Git while ignoring their contents. Run this script once when setting up the project.

### Configuration Files

- `.gitignore` - Configured to track the directory structure but ignore email files and content
- `requirements.txt` - Lists the Python package dependencies

## Limitations

- The tool is designed for English-language emails
- Complex HTML formatting may be simplified in the conversion process
- Pattern matching depends on email client formatting and may not detect all thread styles
- Deduplication thresholds may need adjustment for your specific emails
- Very short emails might be incorrectly identified as duplicates (adjust threshold if needed)

## License

This project is licensed under the MIT License - see the LICENSE file for details