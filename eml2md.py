import os
import email
import shutil
import re
import datetime
from email.utils import parsedate_to_datetime
from email.header import decode_header
import quopri
import base64
from pathlib import Path


def decode_content(part):
    """Decode email part content based on its encoding."""
    content = part.get_payload(decode=True)
    charset = part.get_content_charset() or 'utf-8'

    try:
        return content.decode(charset)
    except UnicodeDecodeError:
        # Fallback to utf-8 if specified charset fails
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # Last resort: ignore problematic characters
            return content.decode('utf-8', errors='ignore')


def decode_email_header(header):
    """Decode email header."""
    if header is None:
        return ""

    decoded_parts = []
    for content, encoding in decode_header(header):
        if isinstance(content, bytes):
            if encoding:
                try:
                    decoded_parts.append(content.decode(encoding))
                except (UnicodeDecodeError, LookupError):
                    # Fallback if specified encoding fails
                    decoded_parts.append(content.decode('utf-8', errors='ignore'))
            else:
                decoded_parts.append(content.decode('utf-8', errors='ignore'))
        else:
            decoded_parts.append(content)

    return "".join(decoded_parts)


def extract_email_parts(msg):
    """Extract relevant parts from an email message."""
    # Extract headers
    date_str = msg.get('Date')
    date = None
    if date_str:
        try:
            date = parsedate_to_datetime(date_str)
        except:
            date = None

    from_addr = decode_email_header(msg.get('From', ''))
    to_addr = decode_email_header(msg.get('To', ''))
    cc_addr = decode_email_header(msg.get('Cc', ''))
    subject = decode_email_header(msg.get('Subject', ''))

    # Extract body content and attachments
    body_text = ""
    attachments = []

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = part.get('Content-Disposition', '')

        # Handle text parts
        if content_type == 'text/plain' and 'attachment' not in content_disposition:
            body_text += decode_content(part)

        # Handle HTML parts if no plain text is available
        elif content_type == 'text/html' and 'attachment' not in content_disposition and not body_text:
            # Basic HTML stripping (simple approach)
            html_content = decode_content(part)
            # Remove HTML tags (simple approach)
            body_text += re.sub(r'<[^>]+>', '', html_content)

        # Handle attachments
        elif 'attachment' in content_disposition or part.get_filename():
            filename = part.get_filename()
            if filename:
                filename = decode_email_header(filename)
                attachment_content = part.get_payload(decode=True)
                if attachment_content:
                    attachments.append((filename, attachment_content, content_type))

    return {
        'date': date,
        'from': from_addr,
        'to': to_addr,
        'cc': cc_addr,
        'subject': subject,
        'body': body_text,
        'attachments': attachments
    }


def create_markdown_content(emails):
    """Create markdown content from extracted email parts."""
    # Sort emails by date
    sorted_emails = sorted(emails, key=lambda x: x['date'] if x['date'] else datetime.datetime.min)

    markdown_content = "# Email Thread\n\n"

    for idx, email_parts in enumerate(sorted_emails, 1):
        markdown_content += f"## Email {idx}\n\n"

        # Add metadata
        if email_parts['date']:
            markdown_content += f"**Date**: {email_parts['date'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        markdown_content += f"**From**: {email_parts['from']}\n\n"
        markdown_content += f"**To**: {email_parts['to']}\n\n"

        if email_parts['cc']:
            markdown_content += f"**CC**: {email_parts['cc']}\n\n"

        markdown_content += f"**Subject**: {email_parts['subject']}\n\n"

        # Add body content
        markdown_content += "### Content\n\n"
        markdown_content += email_parts['body'].strip() + "\n\n"

        # Add attachments info
        if email_parts['attachments']:
            markdown_content += "### Attachments\n\n"
            for attachment_name, _, _ in email_parts['attachments']:
                markdown_content += f"- [{attachment_name}]({attachment_name})\n"
            markdown_content += "\n"

        markdown_content += "---\n\n"

    return markdown_content


def process_eml_file(eml_file_path):
    """Process an EML file and convert it to Markdown with attachments."""
    # Create output directory name based on EML filename
    eml_basename = os.path.basename(eml_file_path)
    output_dir_name = os.path.splitext(eml_basename)[0]
    output_dir_path = os.path.join('output', output_dir_name)
    os.makedirs(output_dir_path, exist_ok=True)

    # Parse the EML file
    with open(eml_file_path, 'rb') as file:
        msg = email.message_from_binary_file(file)

    # Handle single email or multiple emails in a thread
    if msg.get_content_type() == 'multipart/mixed' and any(
            part.get_content_type() == 'message/rfc822' for part in msg.walk()):
        # This might be a thread with forwarded messages
        emails = []

        # Extract the main email
        main_email = extract_email_parts(msg)
        emails.append(main_email)

        # Extract embedded emails
        for part in msg.walk():
            if part.get_content_type() == 'message/rfc822':
                embedded_msgs = part.get_payload()
                if isinstance(embedded_msgs, list):
                    for embedded_msg in embedded_msgs:
                        emails.append(extract_email_parts(embedded_msg))
    else:
        # Single email
        emails = [extract_email_parts(msg)]

    # Create markdown content
    markdown_content = create_markdown_content(emails)

    # Save markdown file
    md_file_path = os.path.join(output_dir_path, f"{output_dir_name}.md")
    with open(md_file_path, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_content)

    # Save attachments
    for email_parts in emails:
        for attachment_name, attachment_content, _ in email_parts['attachments']:
            # Sanitize filename to avoid path issues
            safe_filename = re.sub(r'[^\w\.-]', '_', attachment_name)
            attachment_path = os.path.join(output_dir_path, safe_filename)

            with open(attachment_path, 'wb') as attachment_file:
                attachment_file.write(attachment_content)

    # Move processed EML file to 'done' directory
    done_dir = 'done'
    os.makedirs(done_dir, exist_ok=True)
    shutil.move(eml_file_path, os.path.join(done_dir, eml_basename))

    return md_file_path


def main():
    """Main function to process all EML files in the input directory."""
    # Create required directories if they don't exist
    for directory in ['input', 'output', 'done']:
        os.makedirs(directory, exist_ok=True)

    # Process all EML files in the input directory
    input_dir = 'input'
    processed_files = []

    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.eml'):
            eml_file_path = os.path.join(input_dir, filename)
            try:
                md_file_path = process_eml_file(eml_file_path)
                processed_files.append((filename, md_file_path))
                print(f"Processed: {filename} -> {md_file_path}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

    # Print summary
    print("\nConversion Summary:")
    print(f"Total files processed: {len(processed_files)}")
    for original, converted in processed_files:
        print(f"  {original} -> {converted}")


if __name__ == "__main__":
    main()