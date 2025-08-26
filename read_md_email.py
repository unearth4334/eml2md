#!/usr/bin/env python3
import re
import sys
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# Optional dependency for cross-platform clipboard
try:
    import pyperclip  # type: ignore
    _HAS_PYPERCLIP = True
except Exception:
    _HAS_PYPERCLIP = False

DATE_IN_FMT = "%Y-%m-%d %H:%M:%S"
DATE_OUT_FMT = "%Y-%m-%d %H:%M"  # Obsidian frontmatter format (no seconds)

# ----------------------- Helpers -----------------------
def _clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def _strip_subject_prefixes(subject: str) -> str:
    """Remove common reply/forward prefixes (Re:/Fw:/Fwd:) repeatedly."""
    if not subject:
        return ""
    s = subject.strip()
    while True:
        new = re.sub(r"^(?:(re|fw|fwd)\s*:\s*)", "", s, flags=re.IGNORECASE)
        if new == s:
            break
        s = new
    return s

def _normalize_name_email_glue(s: str) -> str:
    """Fix artifacts like "Name, <email>" and join wrapped lines."""
    s = re.sub(r"[\r\n\t]+", " ", s)            # collapse newlines/tabs
    s = re.sub(r"\b,\s*(<[^>]+>)", r" \1", s)     # remove stray comma before <email>
    s = re.sub(r"\s{2,}", " ", s).strip()          # dedupe spaces
    return s

def _parse_recipients_list(field: str) -> list:
    """Return a clean list like ["Name <email>", ...] from a To/CC field.
    Robust to newlines, stray commas/semicolons, and wrapped names.
    Avoids leaving leading "; " or ", " on items.
    """
    if not field:
        return []
    s = _normalize_name_email_glue(field)

    recipients = []
    used_spans = []

    # 1) Capture Name <email> with an optional separator before it so we don't keep leading ';' or ','
    name_email_pat = re.compile(r'(?:^|[;,])\s*([^<>",;]+?)\s*<([^>]+)>')
    for m in name_email_pat.finditer(s):
        name = _clean_ws(m.group(1))
        email = _clean_ws(m.group(2))
        item = f"{name} <{email}>"
        recipients.append(item)
        used_spans.append(m.span())

    # Mask consumed spans to avoid double-counting
    masked = list(s)
    for a, b in used_spans:
        for i in range(a, b):
            masked[i] = "\0"
    masked = "".join(masked)

    # 2) Add any bare emails left
    for m in re.finditer(r"(?<![<@])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", masked):
        recipients.append(m.group(1))

    # 3) Fallback split if nothing matched
    if not recipients:
        parts = [p.strip() for p in re.split(r"[;,]", s) if p.strip()]
        recipients.extend(parts)

    # 4) Clean any accidental leading separators (belt & suspenders)
    recipients = [re.sub(r'^[,;]\s*', '', r).strip() for r in recipients]

    # De-dup while preserving order
    seen = set()
    uniq = []
    for r in recipients:
        if r and r not in seen:
            uniq.append(r)
            seen.add(r)
    return uniq

def _shorten_preview_list(recipients: list) -> str:
    if not recipients:
        return ""
    if len(recipients) > 3:
        return f"{recipients[0]}, {recipients[1]}, {recipients[2]}, and {len(recipients)-3} others..."
    return ", ".join(recipients)

def _first_n_words(text: str, n: int = 20) -> str:
    words = _clean_ws(text).split()
    return " ".join(words[:n])

# ----------------------- Parsing -----------------------
def parse_emails(md_text: str):
    chunks = re.split(r"(?=^## Email\s+\d+\s*$)", md_text, flags=re.MULTILINE)
    emails = []

    for chunk in chunks:
        if not chunk.strip():
            continue

        num_m = re.search(r"^## Email\s+(\d+)\s*$", chunk, flags=re.MULTILINE)
        email_number = int(num_m.group(1)) if num_m else None

        date_m = re.search(r"\*\*Date\*\*:\s*(.+)", chunk)
        from_m = re.search(r"\*\*From\*\*:\s*(.+)", chunk)
        to_m = re.search(r"\*\*To\*\*:\s*(.+?)(?=\n\*\*(CC|Subject)\*\*:|\n###|$)", chunk, flags=re.DOTALL)
        cc_m = re.search(r"\*\*CC\*\*:\s*(.+?)(?=\n\*\*Subject\*\*:|\n###|$)", chunk, flags=re.DOTALL)
        subj_m = re.search(r"\*\*Subject\*\*:\s*(.+)", chunk)
        content_m = re.search(r"### Content\s*\n(.+?)(?=\n-{3,}|\n## |\n### Attachments|$)", chunk, flags=re.DOTALL)

        if not (date_m or from_m or subj_m or content_m):
            continue

        date_raw = _clean_ws(date_m.group(1)) if date_m else ""
        date_obj = None
        date_out = ""
        if date_raw:
            try:
                date_obj = datetime.strptime(date_raw, DATE_IN_FMT)
                date_out = date_obj.strftime(DATE_OUT_FMT)
            except ValueError:
                pass

        to_list = _parse_recipients_list(to_m.group(1) if to_m else "")
        cc_list = _parse_recipients_list(cc_m.group(1) if cc_m else "")

        subject = _strip_subject_prefixes(_clean_ws(subj_m.group(1)) if subj_m else "")

        content_raw = (content_m.group(1).strip() if content_m else "").strip()
        # Remove quoted history after underscore separators
        split_pos = None
        m_sep = re.search(r"^_{6,}.*$", content_raw, flags=re.MULTILINE)
        if m_sep:
            split_pos = m_sep.start()
        else:
            token = "________________________________"
            p = content_raw.find(token)
            if p != -1:
                split_pos = p
        content_clean = content_raw[:split_pos].rstrip() if split_pos is not None else content_raw

        emails.append({
            "email_number": email_number,
            "date_in": date_raw,
            "date_out": date_out,
            "date": date_obj,
            "from": _clean_ws(from_m.group(1)) if from_m else "",
            "to_list": to_list,   # full list for YAML
            "cc_list": cc_list,   # full list for YAML
            "subject": subject,
            "content": content_clean,
        })

    # Sort newest first (undated go last)
    def sort_key(e):
        return e["date"].timestamp() if e["date"] else float("-inf")

    emails.sort(key=sort_key, reverse=True)
    return emails

# ----------------------- UI -----------------------
def preview_emails(emails):
    for idx, e in enumerate(emails, start=1):
        label = f"Email {e['email_number']}" if e['email_number'] is not None else "Email ?"
        print(f"[{idx}] {label}")
        print(f"----Date: {e['date_in']}")
        print(f"----From: {e['from']}")
        print(f"----To: {_shorten_preview_list(e['to_list'])}")
        print(f"----CC: {_shorten_preview_list(e['cc_list'])}")
        print(f"----Subject: {e['subject']}")
        print("### Content:")
        print(_first_n_words(e["content"], 20))
        print("-" * 70)

def render_obsidian_yaml(email: dict) -> str:
    lines = ["---",
             "email_thread:",
             "aliases: []",
             "type: email",
             "tags:",
             "  - "]

    if email['date_out']:
        date_part, time_part = email['date_out'].split(' ')
        lines.append(f"date: {date_part}")
        lines.append(f"time: {time_part}")
    elif email['date_in']:
        # Fallback: try to split date_in if possible
        parts = email['date_in'].split(' ')
        if len(parts) >= 2:
            lines.append(f"date: {parts[0]}")
            lines.append(f"time: {parts[1]}")
        else:
            lines.append(f"date: {email['date_in']}")
    lines.append(f"sender: {email['from']}")

    lines.append("to:")
    for r in email["to_list"]:
        lines.append(f"  - {r}")

    if email["cc_list"]:
        lines.append("cc:")
        for r in email["cc_list"]:
            lines.append(f"  - {r}")

    subj = email['subject'].replace('"', '\\"')
    lines.append(f"subject: \"{subj}\"")
    lines.append("---\n")
    return "\n".join(lines)

# ----------------------- Clipboard -----------------------
def copy_to_clipboard(text: str):
    # Try pyperclip first
    try:
        import pyperclip  # re-import inside to ensure availability when packaged
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    # Fallback to Tk clipboard
    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False

# ----------------------- Main -----------------------
def main():
    # File picker
    root = tk.Tk()
    root.withdraw()
    md_path = filedialog.askopenfilename(
        filetypes=[("Markdown Files", "*.md")],
        title="Select a Markdown file"
    )
    if not md_path:
        print("No file selected.")
        sys.exit(1)

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    emails = parse_emails(md_text)
    if not emails:
        print("No emails found.")
        sys.exit(1)

    preview_emails(emails)

    try:
        sel = int(input("Enter email index number: ").strip())
        if not (1 <= sel <= len(emails)):
            raise ValueError
    except ValueError:
        print("Invalid selection.")
        sys.exit(1)

    chosen = emails[sel - 1]

    # Construct Obsidian-ready note (FULL recipient lists)
    result = render_obsidian_yaml(chosen) + chosen["content"].rstrip() + "\n"

    print("\n" + "=" * 40 + "\n")
    print(result)

    if copy_to_clipboard(result):
        print("\n(The email with full properties has been copied to your clipboard.)")
    else:
        print("\n(Clipboard copy failed. You can still copy from the console output.)")

if __name__ == "__main__":
    main()
