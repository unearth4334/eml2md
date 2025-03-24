# EML to Markdown Converter

This tool converts email files (`.eml`) to Markdown format (`.md`) while preserving the email thread structure and extracting attachments.

## Features

- Converts `.eml` files to Markdown format
- Preserves email thread structure using two methods:
  - Standard RFC822 embedded message detection
  - Pattern matching to detect quoted emails in the body text
- Extracts and saves attachments
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

1. Place your `.eml` files in the `input` directory
2. Run the script:

```bash
# Default: oldest to newest email order
python eml2md.py

# Optional: newest to oldest email order
python eml2md.py --newest-first
```

3. Find your converted files in the `output` directory, organized in subdirectories named after the original email files

### Command Line Options

| Option | Description |
|--------|-------------|
| `--newest-first` | Sort emails from newest to oldest in the markdown file (default is oldest to newest) |

## Output Format

The generated Markdown file includes:

- Email thread organized chronologically
- Metadata for each email (date, from, to, cc, subject)
- Email content
- Links to extracted attachments

## Thread Detection

The tool uses two methods to detect email threads:

1. **Embedded Messages**: Detects properly formatted `message/rfc822` parts in multipart emails
2. **Pattern Matching**: Analyzes the email body text to find patterns indicating quoted emails such as:
   - Outlook format: "From: ... Sent: ... To: ... Subject: ..."
   - Reply format: "On [date], [person] wrote:"
   - Gmail format: "On [date] at [time], [person] wrote:"

### Caveats for Thread Detection

- Pattern matching is not 100% reliable and depends on email client formatting
- Different email clients use different quoting styles which may not be detected
- Date parsing from text may not always be accurate
- The original formatting of quoted text might be altered
- Some false positives may occur if the email body contains text that matches the patterns
- Deeply nested conversations might not be fully reconstructed

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

### Utility Scripts

- `create_gitkeep.py` - Sets up the required directory structure and creates .gitkeep files to ensure the directories are tracked by Git while ignoring their contents. Run this script once when setting up the project.

### Configuration Files

- `.gitignore` - Configured to track the directory structure but ignore email files and content
- `requirements.txt` - Lists the Python package dependencies

## Limitations

- The tool is designed for English-language emails
- Complex HTML formatting may be simplified in the conversion process
- Email threads are reconstructed based on date/time, which may not always match the original thread structure
- Thread detection through pattern matching may miss some quoted emails or incorrectly identify parts of the content as separate emails

## License

This project is licensed under the MIT License - see the LICENSE file for details