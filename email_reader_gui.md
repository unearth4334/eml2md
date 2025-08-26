# Email Reader GUI (DataviewJS)

This is an Obsidian-based GUI for reading and extracting individual emails from email thread markdown files. It provides the same functionality as the Python `read_md_email.py` script but runs entirely within Obsidian using DataviewJS.

## Instructions

1. **Save this file** in your Obsidian vault
2. **Enable the Dataview plugin** in Obsidian Community Plugins
3. **Open this note** in Obsidian
4. The GUI interface will appear below

## Features

- Browse and select markdown files containing email threads
- Parse and display email previews
- Select emails to extract
- Generate Obsidian-formatted YAML frontmatter + content
- Copy results to clipboard

---

```dataviewjs
// Email Reader GUI DataviewJS Implementation
// Replicates the functionality of read_md_email.py

class EmailReaderGUI {
    constructor() {
        this.emails = [];
        this.selectedFile = null;
        this.container = null;
    }

    // Helper functions (equivalent to Python helpers)
    cleanWhitespace(text) {
        return text ? text.replace(/\s+/g, ' ').trim() : '';
    }

    stripSubjectPrefixes(subject) {
        if (!subject) return '';
        let s = subject.trim();
        while (true) {
            const newS = s.replace(/^(?:(re|fw|fwd)\s*:\s*)/i, '');
            if (newS === s) break;
            s = newS;
        }
        return s;
    }

    normalizeNameEmailGlue(s) {
        s = s.replace(/[\r\n\t]+/g, ' ');  // collapse newlines/tabs
        s = s.replace(/\b,\s*(<[^>]+>)/g, ' $1');  // remove stray comma before <email>
        s = s.replace(/\s{2,}/g, ' ').trim();  // dedupe spaces
        return s;
    }

    parseRecipientsList(field) {
        if (!field) return [];
        const s = this.normalizeNameEmailGlue(field);
        const recipients = [];
        const usedSpans = [];

        // 1) Capture Name <email> patterns
        const nameEmailRegex = /(?:^|[;,])\s*([^<>",;]+?)\s*<([^>]+)>/g;
        let match;
        while ((match = nameEmailRegex.exec(s)) !== null) {
            const name = this.cleanWhitespace(match[1]);
            const email = this.cleanWhitespace(match[2]);
            const item = `${name} <${email}>`;
            recipients.push(item);
            usedSpans.push([match.index, match.index + match[0].length]);
        }

        // Mask consumed spans
        let masked = s.split('');
        for (const [start, end] of usedSpans) {
            for (let i = start; i < end; i++) {
                masked[i] = '\0';
            }
        }
        masked = masked.join('');

        // 2) Add any bare emails left
        const emailRegex = /(?<![<@])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})/g;
        while ((match = emailRegex.exec(masked)) !== null) {
            recipients.push(match[1]);
        }

        // 3) Fallback split if nothing matched
        if (recipients.length === 0) {
            const parts = s.split(/[;,]/).map(p => p.trim()).filter(p => p);
            recipients.push(...parts);
        }

        // 4) Clean any accidental leading separators
        const cleaned = recipients.map(r => r.replace(/^[,;]\s*/, '').trim());

        // De-duplicate while preserving order
        const seen = new Set();
        const unique = [];
        for (const r of cleaned) {
            if (r && !seen.has(r)) {
                unique.push(r);
                seen.add(r);
            }
        }
        return unique;
    }

    shortenPreviewList(recipients) {
        if (!recipients || recipients.length === 0) return '';
        if (recipients.length > 3) {
            return `${recipients[0]}, ${recipients[1]}, ${recipients[2]}, and ${recipients.length - 3} others...`;
        }
        return recipients.join(', ');
    }

    firstNWords(text, n = 20) {
        const words = this.cleanWhitespace(text).split(' ');
        return words.slice(0, n).join(' ');
    }

    parseEmails(mdText) {
        const chunks = mdText.split(/(?=^## Email\s+\d+\s*$)/m);
        const emails = [];

        for (const chunk of chunks) {
            if (!chunk.trim()) continue;

            const numMatch = chunk.match(/^## Email\s+(\d+)\s*$/m);
            const emailNumber = numMatch ? parseInt(numMatch[1]) : null;

            const dateMatch = chunk.match(/\*\*Date\*\*:\s*(.+)/);
            const fromMatch = chunk.match(/\*\*From\*\*:\s*(.+)/);
            const toMatch = chunk.match(/\*\*To\*\*:\s*(.+?)(?=\n\*\*(CC|Subject)\*\*:|\n###|$)/s);
            const ccMatch = chunk.match(/\*\*CC\*\*:\s*(.+?)(?=\n\*\*Subject\*\*:|\n###|$)/s);
            const subjMatch = chunk.match(/\*\*Subject\*\*:\s*(.+)/);
            const contentMatch = chunk.match(/### Content\s*\n(.+?)(?=\n-{3,}|\n## |\n### Attachments|$)/s);

            if (!(dateMatch || fromMatch || subjMatch || contentMatch)) {
                continue;
            }

            const dateRaw = dateMatch ? this.cleanWhitespace(dateMatch[1]) : '';
            let dateObj = null;
            let dateOut = '';
            
            if (dateRaw) {
                try {
                    // Try to parse the date (simplified)
                    dateObj = new Date(dateRaw);
                    if (!isNaN(dateObj.getTime())) {
                        // Format as YYYY-MM-DD HH:MM
                        dateOut = dateObj.toISOString().slice(0, 16).replace('T', ' ');
                    }
                } catch (e) {
                    // Date parsing failed, keep original
                }
            }

            const toList = this.parseRecipientsList(toMatch ? toMatch[1] : '');
            const ccList = this.parseRecipientsList(ccMatch ? ccMatch[1] : '');
            const subject = this.stripSubjectPrefixes(subjMatch ? this.cleanWhitespace(subjMatch[1]) : '');

            let contentRaw = contentMatch ? contentMatch[1].trim() : '';
            
            // Remove quoted history after underscore separators
            let splitPos = null;
            const sepMatch = contentRaw.match(/^_{6,}.*$/m);
            if (sepMatch) {
                splitPos = sepMatch.index;
            } else {
                const token = '________________________________';
                const p = contentRaw.indexOf(token);
                if (p !== -1) {
                    splitPos = p;
                }
            }
            const contentClean = splitPos !== null ? contentRaw.slice(0, splitPos).trim() : contentRaw;

            emails.push({
                emailNumber,
                dateIn: dateRaw,
                dateOut,
                date: dateObj,
                from: fromMatch ? this.cleanWhitespace(fromMatch[1]) : '',
                toList,
                ccList,
                subject,
                content: contentClean
            });
        }

        // Sort newest first (undated go last)
        emails.sort((a, b) => {
            const aTime = a.date ? a.date.getTime() : -Infinity;
            const bTime = b.date ? b.date.getTime() : -Infinity;
            return bTime - aTime;
        });

        return emails;
    }

    renderObsidianYaml(email) {
        const lines = [
            '---',
            'email_thread:',
            'aliases: []',
            'type: email',
            'tags:',
            '  - '
        ];

        if (email.dateOut) {
            const [datePart, timePart] = email.dateOut.split(' ');
            lines.push(`date: ${datePart}`);
            lines.push(`time: ${timePart}`);
        } else if (email.dateIn) {
            const parts = email.dateIn.split(' ');
            if (parts.length >= 2) {
                lines.push(`date: ${parts[0]}`);
                lines.push(`time: ${parts[1]}`);
            } else {
                lines.push(`date: ${email.dateIn}`);
            }
        }
        
        lines.push(`sender: ${email.from}`);
        
        lines.push('to:');
        for (const recipient of email.toList) {
            lines.push(`  - ${recipient}`);
        }

        if (email.ccList && email.ccList.length > 0) {
            lines.push('cc:');
            for (const recipient of email.ccList) {
                lines.push(`  - ${recipient}`);
            }
        }

        const escapedSubject = email.subject.replace(/"/g, '\\"');
        lines.push(`subject: "${escapedSubject}"`);
        lines.push('---\n');
        
        return lines.join('\n');
    }

    async getMarkdownFiles() {
        // Get all markdown files in the vault
        const files = app.vault.getMarkdownFiles();
        return files.filter(file => 
            file.path.endsWith('.md') && 
            !file.path.includes('email_reader_gui.md') // Exclude this file
        );
    }

    async loadFileContent(file) {
        try {
            return await app.vault.read(file);
        } catch (error) {
            console.error('Error reading file:', error);
            return null;
        }
    }

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            return false;
        }
    }

    createFileSelector() {
        const selector = this.container.createEl('div', { cls: 'email-file-selector' });
        selector.createEl('h3', { text: 'Select Email Thread File' });
        
        const fileSelect = selector.createEl('select', { cls: 'email-file-select' });
        fileSelect.createEl('option', { text: 'Choose a markdown file...', value: '' });
        
        const loadButton = selector.createEl('button', { 
            text: 'Load Emails',
            cls: 'email-load-button'
        });
        loadButton.disabled = true;

        // Populate file list
        this.getMarkdownFiles().then(files => {
            for (const file of files) {
                const option = fileSelect.createEl('option', { 
                    text: file.path,
                    value: file.path
                });
            }
        });

        fileSelect.addEventListener('change', () => {
            loadButton.disabled = !fileSelect.value;
        });

        loadButton.addEventListener('click', async () => {
            const selectedPath = fileSelect.value;
            if (!selectedPath) return;

            const file = app.vault.getAbstractFileByPath(selectedPath);
            if (!file) {
                selector.createEl('div', { 
                    text: 'Error: File not found',
                    cls: 'email-error'
                });
                return;
            }

            const content = await this.loadFileContent(file);
            if (content) {
                this.selectedFile = file;
                this.emails = this.parseEmails(content);
                this.showEmailList();
            } else {
                selector.createEl('div', { 
                    text: 'Error: Could not read file',
                    cls: 'email-error'
                });
            }
        });

        return selector;
    }

    showEmailList() {
        // Clear previous content
        const existingList = this.container.querySelector('.email-list-container');
        if (existingList) {
            existingList.remove();
        }

        if (this.emails.length === 0) {
            this.container.createEl('div', {
                text: 'No emails found in the selected file.',
                cls: 'email-error'
            });
            return;
        }

        const listContainer = this.container.createEl('div', { cls: 'email-list-container' });
        listContainer.createEl('h3', { text: `Found ${this.emails.length} emails` });

        const emailList = listContainer.createEl('div', { cls: 'email-list' });

        this.emails.forEach((email, index) => {
            const emailItem = emailList.createEl('div', { cls: 'email-item' });
            
            const label = email.emailNumber !== null ? `Email ${email.emailNumber}` : 'Email ?';
            const header = emailItem.createEl('div', { cls: 'email-header' });
            header.createEl('strong', { text: `[${index + 1}] ${label}` });
            
            const details = emailItem.createEl('div', { cls: 'email-details' });
            details.createEl('div', { text: `Date: ${email.dateIn}` });
            details.createEl('div', { text: `From: ${email.from}` });
            details.createEl('div', { text: `To: ${this.shortenPreviewList(email.toList)}` });
            details.createEl('div', { text: `CC: ${this.shortenPreviewList(email.ccList)}` });
            details.createEl('div', { text: `Subject: ${email.subject}` });
            
            const contentPreview = details.createEl('div', { cls: 'email-content-preview' });
            contentPreview.createEl('strong', { text: 'Content: ' });
            contentPreview.createSpan({ text: this.firstNWords(email.content, 20) });

            const selectButton = emailItem.createEl('button', {
                text: 'Extract This Email',
                cls: 'email-select-button'
            });

            selectButton.addEventListener('click', () => {
                this.extractEmail(email, index);
            });
        });
    }

    extractEmail(email, index) {
        // Clear previous output
        const existingOutput = this.container.querySelector('.email-output-container');
        if (existingOutput) {
            existingOutput.remove();
        }

        const outputContainer = this.container.createEl('div', { cls: 'email-output-container' });
        outputContainer.createEl('h3', { text: `Extracted Email ${index + 1}` });

        const result = this.renderObsidianYaml(email) + email.content.trim() + '\n';

        const outputArea = outputContainer.createEl('textarea', {
            cls: 'email-output-text',
            attr: { 
                readonly: true,
                rows: Math.min(result.split('\n').length + 2, 25)
            }
        });
        outputArea.value = result;

        const buttonContainer = outputContainer.createEl('div', { cls: 'email-button-container' });
        
        const copyButton = buttonContainer.createEl('button', {
            text: 'Copy to Clipboard',
            cls: 'email-copy-button'
        });

        const newNoteButton = buttonContainer.createEl('button', {
            text: 'Create New Note',
            cls: 'email-new-note-button'
        });

        const backButton = buttonContainer.createEl('button', {
            text: 'Back to Email List',
            cls: 'email-back-button'
        });

        copyButton.addEventListener('click', async () => {
            const success = await this.copyToClipboard(result);
            if (success) {
                copyButton.textContent = 'Copied!';
                setTimeout(() => {
                    copyButton.textContent = 'Copy to Clipboard';
                }, 2000);
            } else {
                copyButton.textContent = 'Copy Failed';
                setTimeout(() => {
                    copyButton.textContent = 'Copy to Clipboard';
                }, 2000);
            }
        });

        newNoteButton.addEventListener('click', async () => {
            const fileName = `Email - ${email.subject || 'Untitled'} - ${new Date().toISOString().slice(0, 10)}.md`;
            const sanitizedFileName = fileName.replace(/[<>:"/\\|?*]/g, '-');
            
            try {
                const newFile = await app.vault.create(sanitizedFileName, result);
                await app.workspace.openLinkText(sanitizedFileName, '', true);
                newNoteButton.textContent = 'Note Created!';
                setTimeout(() => {
                    newNoteButton.textContent = 'Create New Note';
                }, 2000);
            } catch (error) {
                console.error('Error creating note:', error);
                newNoteButton.textContent = 'Creation Failed';
                setTimeout(() => {
                    newNoteButton.textContent = 'Create New Note';
                }, 2000);
            }
        });

        backButton.addEventListener('click', () => {
            outputContainer.remove();
        });
    }

    render(container) {
        this.container = container;
        
        // Add styles
        const style = container.createEl('style');
        style.textContent = `
            .email-file-selector {
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid var(--background-modifier-border);
                border-radius: 6px;
                background: var(--background-secondary);
            }
            
            .email-file-select {
                width: 100%;
                margin: 10px 0;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid var(--background-modifier-border);
            }
            
            .email-load-button {
                padding: 8px 16px;
                background: var(--interactive-accent);
                color: var(--text-on-accent);
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .email-load-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .email-list {
                max-height: 600px;
                overflow-y: auto;
                border: 1px solid var(--background-modifier-border);
                border-radius: 6px;
            }
            
            .email-item {
                padding: 15px;
                border-bottom: 1px solid var(--background-modifier-border);
                background: var(--background-primary);
            }
            
            .email-item:last-child {
                border-bottom: none;
            }
            
            .email-header {
                margin-bottom: 10px;
                color: var(--text-accent);
            }
            
            .email-details {
                font-size: 0.9em;
                margin-bottom: 10px;
                line-height: 1.4;
            }
            
            .email-details > div {
                margin-bottom: 4px;
            }
            
            .email-content-preview {
                margin-top: 8px;
                font-style: italic;
                color: var(--text-muted);
            }
            
            .email-select-button {
                margin-top: 10px;
                padding: 6px 12px;
                background: var(--interactive-accent);
                color: var(--text-on-accent);
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
            }
            
            .email-output-container {
                margin-top: 20px;
                padding: 15px;
                border: 1px solid var(--background-modifier-border);
                border-radius: 6px;
                background: var(--background-secondary);
            }
            
            .email-output-text {
                width: 100%;
                margin: 15px 0;
                padding: 10px;
                font-family: var(--font-monospace);
                font-size: 0.85em;
                border: 1px solid var(--background-modifier-border);
                border-radius: 4px;
                background: var(--background-primary);
                resize: vertical;
            }
            
            .email-button-container {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            
            .email-copy-button, .email-new-note-button, .email-back-button {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
            }
            
            .email-copy-button {
                background: var(--interactive-accent);
                color: var(--text-on-accent);
            }
            
            .email-new-note-button {
                background: var(--interactive-success);
                color: var(--text-on-accent);
            }
            
            .email-back-button {
                background: var(--background-modifier-border);
                color: var(--text-normal);
            }
            
            .email-error {
                color: var(--text-error);
                margin: 10px 0;
                padding: 10px;
                background: var(--background-modifier-error);
                border-radius: 4px;
            }
        `;
        
        // Create main interface
        container.createEl('h2', { text: 'Email Reader GUI' });
        container.createEl('p', { 
            text: 'Select a markdown file containing email threads to extract individual emails with Obsidian formatting.'
        });
        
        this.createFileSelector();
    }
}

// Initialize and render the GUI
const emailGUI = new EmailReaderGUI();
emailGUI.render(this.container);
```