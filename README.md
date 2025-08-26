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

### Email Reader GUI

For reading and extracting individual emails from converted markdown files, use the Obsidian-based DataviewJS GUI:

1. Install [Obsidian](https://obsidian.md/) and enable the Dataview plugin
2. Copy `email_reader_gui.md` to your Obsidian vault  
3. Open the file in Obsidian - the GUI will appear automatically
4. Select markdown files, browse emails, and extract them with Obsidian formatting

See `DATAVIEWJS_README.md` for detailed setup instructions.


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

## Project Components

### Main Script

- `eml2md.py` - The main script that handles the conversion process

### GUI Application

#### DataviewJS GUI (Obsidian)
- `email_reader_gui.md` - Obsidian DataviewJS implementation for reading and extracting emails
- `DATAVIEWJS_README.md` - Setup and usage instructions for the DataviewJS GUI
- `sample_email_thread.md` - Sample email data for testing

### Email Reader Utilities

- `read_md_email.py` - Python script for reading and extracting emails from markdown files (tkinter version)

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