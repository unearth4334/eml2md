import os
import email
import shutil
import re
import datetime
import binascii
from email.utils import parsedate_to_datetime
from email.header import decode_header


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


def extract_thread_parts(body_text):
    """
    Extract email thread parts from plain text body by identifying common
    email client quotation patterns.

    Returns a list of dictionaries containing extracted metadata and content for each part.
    """
    thread_parts = []

    # Common patterns that indicate the start of a quoted email in the thread
    patterns = [
        # Common Outlook format
        r'From:[\s]*(.*?)[\r\n]+Sent:[\s]*(.*?)[\r\n]+To:[\s]*(.*?)(?:[\r\n]+Cc:[\s]*(.*?))?[\r\n]+Subject:[\s]*(.*?)[\r\n]+',
        # Alternative format sometimes seen
        r'On[\s]*(.*?),[\s]*(.*?)[\s]+wrote:[\r\n]+',
        # Gmail-style format
        r'On[\s]*(.*?)[\s]+at[\s]+(.*?),[\s]*(.*?)[\s]+wrote:[\r\n]+'
    ]

    # Find all occurrences of email headers in the body text
    for pattern in patterns:
        matches = list(re.finditer(pattern, body_text, re.IGNORECASE | re.DOTALL))
        if matches:
            last_end = 0
            for match in matches:
                # Extract metadata from the match
                if "From:" in pattern:
                    # Outlook format
                    email_part = {
                        'from': match.group(1).strip() if match.group(1) else "",
                        'date': match.group(2).strip() if match.group(2) else "",
                        'to': match.group(3).strip() if match.group(3) else "",
                        'cc': match.group(4).strip() if len(match.groups()) >= 4 and match.group(4) else "",
                        'subject': match.group(5).strip() if len(match.groups()) >= 5 and match.group(5) else "",
                        'body': ""  # Will be filled with content after the header
                    }
                else:
                    # Other formats
                    email_part = {
                        'from': match.group(3).strip() if len(match.groups()) >= 3 and match.group(3) else match.group(
                            1).strip(),
                        'date': match.group(1).strip() + " " + match.group(2).strip() if match.group(1) and match.group(
                            2) else "",
                        'to': "",
                        'cc': "",
                        'subject': "",
                        'body': ""
                    }

                # Find the end of this part (either the start of the next part or the end of the text)
                next_match = None
                for next_pattern in patterns:
                    next_match_iter = re.search(next_pattern, body_text[match.end():], re.IGNORECASE | re.DOTALL)
                    if next_match_iter:
                        next_match_start = match.end() + next_match_iter.start()
                        if next_match is None or next_match_start < next_match:
                            next_match = next_match_start

                if next_match is None:
                    email_part['body'] = body_text[match.end():].strip()
                else:
                    email_part['body'] = body_text[match.end():next_match].strip()

                thread_parts.append(email_part)

            # If we've found and processed parts with this pattern, we can stop checking other patterns
            if thread_parts:
                break

    return thread_parts


def simhash(text, num_bits=64):
    """
    Generate a SimHash fingerprint for text.

    Args:
        text: The text to hash
        num_bits: The number of bits in the hash

    Returns:
        An integer representing the SimHash fingerprint
    """
    # Clean and normalize the text
    text = re.sub(r'\s+', ' ', text.lower())

    # Extract features (we'll use words and bigrams)
    words = text.split()
    features = words + [' '.join(words[i:i + 2]) for i in range(len(words) - 1)]

    # Initialize vector for hash values
    v = [0] * num_bits

    # For each feature, compute hash and update vector
    for feature in features:
        # Use a consistent hash function
        h = binascii.crc32(feature.encode()) & 0xffffffff

        # Update the vector
        for i in range(num_bits):
            bit = (h >> i) & 1
            v[i] += 1 if bit else -1

    # Convert vector to binary fingerprint
    fingerprint = 0
    for i in range(num_bits):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1, hash2):
    """
    Calculate the Hamming distance between two hashes.

    Args:
        hash1, hash2: Two integer hashes to compare

    Returns:
        The number of bit positions where the bits differ
    """
    xor = hash1 ^ hash2
    return bin(xor).count('1')


def email_feature_hash(email):
    """
    Create a fingerprint of an email for deduplication.

    Args:
        email: An email dictionary containing metadata and body

    Returns:
        A SimHash fingerprint of the email
    """
    # Extract the most important content for comparison
    content = ""

    # From field is very important
    if email.get('from'):
        content += email['from'] + " "

    # Subject is somewhat important
    if email.get('subject'):
        content += email['subject'] + " "

    # For the body, we'll extract key sentences
    body = email.get('body', '')

    # Extract the first few non-empty lines (typically the most distinctive)
    lines = [line.strip() for line in body.split('\n') if line.strip()]
    key_lines = lines[:min(5, len(lines))]

    # Add key lines to content
    content += " ".join(key_lines)

    # Generate SimHash
    return simhash(content)


def deduplicate_emails(emails, threshold=8):
    """
    Remove duplicate emails based on content similarity using SimHash.

    Args:
        emails: List of extracted email parts
        threshold: Maximum Hamming distance to consider as duplicate

    Returns:
        List of unique emails
    """
    if not emails:
        return []

    # Normalize dates for comparison (handle timezone-aware vs timezone-naive)
    for email in emails:
        if isinstance(email.get('date'), datetime.datetime):
            # Convert to naive datetime if it's timezone-aware
            if email['date'].tzinfo is not None:
                # Convert to UTC and then remove timezone info
                email['date'] = email['date'].astimezone(datetime.timezone.utc).replace(tzinfo=None)

    # Calculate hashes for all emails
    email_hashes = [(email, email_feature_hash(email)) for email in emails]

    # Sort by date if available, to prioritize newer emails
    email_hashes.sort(
        key=lambda x: x[0].get('date') if isinstance(x[0].get('date'), datetime.datetime) else datetime.datetime.min,
        reverse=True
    )

    unique_emails = []
    used_indices = set()

    # Iterate through emails
    for i, (email1, hash1) in enumerate(email_hashes):
        if i in used_indices:
            continue

        # Add this email to unique set
        unique_emails.append(email1)
        used_indices.add(i)

        # Mark similar emails as used
        for j, (email2, hash2) in enumerate(email_hashes):
            if j not in used_indices and j != i:
                # Calculate Hamming distance
                distance = hamming_distance(hash1, hash2)
                if distance <= threshold:
                    used_indices.add(j)

    # Sort unique emails by date (already normalized)

    return unique_emails


def create_markdown_content(emails, newest_first=False):
    """Create markdown content from extracted email parts.

    Args:
        emails: List of extracted email parts
        newest_first: If True, sorts emails from newest to oldest. Default is oldest to newest.
    """
    # Note: We assume dates are already normalized before reaching this function

    # Sort emails by date
    sorted_emails = sorted(
        emails,
        key=lambda x: x['date'] if isinstance(x['date'], datetime.datetime) else datetime.datetime.min,
        reverse=newest_first  # Set to True for newest-first, False for oldest-first
    )

    markdown_content = "# Email Thread\n\n"

    for idx, email_parts in enumerate(sorted_emails, 1):
        markdown_content += f"## Email {idx}\n\n"

        # Add metadata
        if email_parts['date']:
            if isinstance(email_parts['date'], datetime.datetime):
                markdown_content += f"**Date**: {email_parts['date'].strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            else:
                markdown_content += f"**Date**: {email_parts['date']}\n\n"

        markdown_content += f"**From**: {email_parts['from']}\n\n"
        markdown_content += f"**To**: {email_parts['to']}\n\n"

        if email_parts['cc']:
            markdown_content += f"**CC**: {email_parts['cc']}\n\n"

        markdown_content += f"**Subject**: {email_parts['subject']}\n\n"

        # Add body content
        markdown_content += "### Content\n\n"
        markdown_content += email_parts['body'].strip() + "\n\n"

        # Add attachments info
        if email_parts.get('attachments') and email_parts['attachments']:
            markdown_content += "### Attachments\n\n"
            for attachment_name, _, _ in email_parts['attachments']:
                markdown_content += f"- [{attachment_name}]({attachment_name})\n"
            markdown_content += "\n"

        markdown_content += "---\n\n"

    return markdown_content


def process_eml_file(eml_file_path, newest_first=False):
    """Process an EML file and convert it to Markdown with attachments.

    Args:
        eml_file_path: Path to the EML file
        newest_first: If True, sorts emails from newest to oldest. Default is oldest to newest.
    """
    # Import here to avoid circular imports
    import dateutil.parser

    # Create output directory name based on EML filename
    eml_basename = os.path.basename(eml_file_path)
    output_dir_name = os.path.splitext(eml_basename)[0]
    output_dir_path = os.path.join('output', output_dir_name)
    os.makedirs(output_dir_path, exist_ok=True)

    # Parse the EML file
    with open(eml_file_path, 'rb') as file:
        msg = email.message_from_binary_file(file)

    # Initialize the emails list
    emails = []

    # First, try to extract embedded emails using the message/rfc822 method
    if msg.get_content_type() == 'multipart/mixed' and any(
            part.get_content_type() == 'message/rfc822' for part in msg.walk()):
        # This is a thread with forwarded messages
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
        # Extract the main email parts
        main_email = extract_email_parts(msg)
        emails.append(main_email)

        # Try to extract additional emails from the body text using pattern matching
        thread_parts = extract_thread_parts(main_email['body'])

        if thread_parts:
            # If thread parts were found, append them to the emails list
            for part in thread_parts:
                # Convert the date string to a datetime object if possible
                date_obj = None
                if part['date']:
                    try:
                        # Try common date formats
                        date_obj = dateutil.parser.parse(part['date'])
                    except:
                        # If parsing fails, keep the string
                        date_obj = part['date']

                # Create an email entry for each thread part
                thread_email = {
                    'date': date_obj,
                    'from': part['from'],
                    'to': part['to'],
                    'cc': part['cc'],
                    'subject': part.get('subject', main_email['subject']),  # Use main subject if not found
                    'body': part['body'],
                    'attachments': []  # Thread parts typically don't have attachments
                }
                emails.append(thread_email)

    # Deduplicate emails using SimHash
    print(f"Found {len(emails)} emails before deduplication")
    unique_emails = deduplicate_emails(emails)
    print(f"Reduced to {len(unique_emails)} unique emails after deduplication")

    # Create markdown content (no need to normalize dates again, they're already normalized)
    markdown_content = create_markdown_content(unique_emails, newest_first)

    # Save markdown file
    md_file_path = os.path.join(output_dir_path, f"{output_dir_name}.md")
    with open(md_file_path, 'w', encoding='utf-8') as md_file:
        md_file.write(markdown_content)

    # Save attachments
    for email_parts in emails:
        for attachment_name, attachment_content, _ in email_parts.get('attachments', []):
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
    import argparse

    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Convert EML files to Markdown format')
    parser.add_argument('--newest-first', action='store_true',
                        help='Sort emails from newest to oldest (default: oldest to newest)')
    parser.add_argument('--dedup-threshold', type=int, default=8,
                        help='Hamming distance threshold for deduplication (default: 8)')
    args = parser.parse_args()

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
                md_file_path = process_eml_file(eml_file_path, args.newest_first)
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