# Email Reader GUI

This interface provides a convenient way to process EML files using the eml2md converter.

## EML to Markdown Converter

Click the button below to run the EML to Markdown converter. This will process all `.eml` files in the `input` directory and convert them to Markdown format.

```dataviewjs
const { exec } = require('child_process');
const path = require('path');

// Create the button
const button = dv.el("button", "Process EML Files", {
    style: "background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin: 10px 0;"
});

// Create status div
const statusDiv = dv.el("div", "", {
    style: "margin-top: 10px; padding: 10px; border-radius: 4px; display: none;"
});

// Add click event listener
button.addEventListener('click', function() {
    // Show processing status
    statusDiv.style.display = "block";
    statusDiv.style.backgroundColor = "#e7f3ff";
    statusDiv.style.color = "#004085";
    statusDiv.textContent = "Processing EML files... Please wait.";
    
    // Disable button during processing
    button.disabled = true;
    button.textContent = "Processing...";
    button.style.backgroundColor = "#cccccc";
    
    // Define the command to run
    const command = 'Emails/eml2md/venv/Scripts/python.exe eml2md.py';
    
    // Execute the command
    exec(command, { cwd: process.cwd() }, (error, stdout, stderr) => {
        // Re-enable button
        button.disabled = false;
        button.textContent = "Process EML Files";
        button.style.backgroundColor = "#4CAF50";
        
        if (error) {
            // Show error status
            statusDiv.style.backgroundColor = "#f8d7da";
            statusDiv.style.color = "#721c24";
            statusDiv.innerHTML = `<strong>Error:</strong> ${error.message}<br><br><strong>Command:</strong> ${command}`;
            console.error('Error executing eml2md:', error);
            return;
        }
        
        if (stderr) {
            // Show warning/stderr
            statusDiv.style.backgroundColor = "#fff3cd";
            statusDiv.style.color = "#856404";
            statusDiv.innerHTML = `<strong>Warning:</strong><br><pre>${stderr}</pre>`;
        }
        
        if (stdout) {
            // Show success status with output
            statusDiv.style.backgroundColor = "#d4edda";
            statusDiv.style.color = "#155724";
            statusDiv.innerHTML = `<strong>Success!</strong> EML files processed successfully.<br><br><strong>Output:</strong><br><pre>${stdout}</pre>`;
        } else if (!stderr) {
            // Show success without output
            statusDiv.style.backgroundColor = "#d4edda";
            statusDiv.style.color = "#155724";
            statusDiv.textContent = "EML files processed successfully!";
        }
    });
});

// Add elements to the page
dv.container.appendChild(button);
dv.container.appendChild(statusDiv);
```

## Alternative Commands

If you need to run the converter with different options, you can use these commands manually:

### Sort emails newest first
```bash
Emails/eml2md/venv/Scripts/python.exe eml2md.py --newest-first
```

### Adjust deduplication threshold
```bash
Emails/eml2md/venv/Scripts/python.exe eml2md.py --dedup-threshold 10
```

### Both options combined
```bash
Emails/eml2md/venv/Scripts/python.exe eml2md.py --newest-first --dedup-threshold 10
```

## Advanced Options Button

```dataviewjs
// Create advanced options section
const advancedSection = dv.el("div", "", {
    style: "margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9;"
});

const advancedTitle = dv.el("h3", "Advanced Options", {
    style: "margin-top: 0; color: #333;"
});

// Newest first checkbox
const newestFirstContainer = dv.el("div", "", {
    style: "margin: 10px 0;"
});
const newestFirstCheckbox = dv.el("input", "", {
    type: "checkbox",
    id: "newestFirst",
    style: "margin-right: 8px;"
});
const newestFirstLabel = dv.el("label", "Sort emails newest first", {
    for: "newestFirst",
    style: "cursor: pointer;"
});

// Dedup threshold input
const dedupContainer = dv.el("div", "", {
    style: "margin: 10px 0;"
});
const dedupLabel = dv.el("label", "Deduplication threshold: ", {
    style: "margin-right: 8px;"
});
const dedupInput = dv.el("input", "", {
    type: "number",
    value: "8",
    min: "1",
    max: "64",
    style: "width: 60px; padding: 4px; border: 1px solid #ddd; border-radius: 2px;"
});

// Advanced run button
const advancedButton = dv.el("button", "Process with Options", {
    style: "background-color: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px;"
});

// Advanced status div
const advancedStatusDiv = dv.el("div", "", {
    style: "margin-top: 10px; padding: 10px; border-radius: 4px; display: none;"
});

// Advanced button click handler
advancedButton.addEventListener('click', function() {
    // Show processing status
    advancedStatusDiv.style.display = "block";
    advancedStatusDiv.style.backgroundColor = "#e7f3ff";
    advancedStatusDiv.style.color = "#004085";
    advancedStatusDiv.textContent = "Processing EML files with advanced options... Please wait.";
    
    // Disable button during processing
    advancedButton.disabled = true;
    advancedButton.textContent = "Processing...";
    advancedButton.style.backgroundColor = "#cccccc";
    
    // Build command with options
    let command = 'Emails/eml2md/venv/Scripts/python.exe eml2md.py';
    
    if (newestFirstCheckbox.checked) {
        command += ' --newest-first';
    }
    
    const threshold = parseInt(dedupInput.value);
    if (threshold && threshold !== 8) {
        command += ` --dedup-threshold ${threshold}`;
    }
    
    // Execute the command
    exec(command, { cwd: process.cwd() }, (error, stdout, stderr) => {
        // Re-enable button
        advancedButton.disabled = false;
        advancedButton.textContent = "Process with Options";
        advancedButton.style.backgroundColor = "#007bff";
        
        if (error) {
            // Show error status
            advancedStatusDiv.style.backgroundColor = "#f8d7da";
            advancedStatusDiv.style.color = "#721c24";
            advancedStatusDiv.innerHTML = `<strong>Error:</strong> ${error.message}<br><br><strong>Command:</strong> ${command}`;
            console.error('Error executing eml2md:', error);
            return;
        }
        
        if (stderr) {
            // Show warning/stderr
            advancedStatusDiv.style.backgroundColor = "#fff3cd";
            advancedStatusDiv.style.color = "#856404";
            advancedStatusDiv.innerHTML = `<strong>Warning:</strong><br><pre>${stderr}</pre>`;
        }
        
        if (stdout) {
            // Show success status with output
            advancedStatusDiv.style.backgroundColor = "#d4edda";
            advancedStatusDiv.style.color = "#155724";
            advancedStatusDiv.innerHTML = `<strong>Success!</strong> EML files processed successfully.<br><br><strong>Command used:</strong> ${command}<br><br><strong>Output:</strong><br><pre>${stdout}</pre>`;
        } else if (!stderr) {
            // Show success without output
            advancedStatusDiv.style.backgroundColor = "#d4edda";
            advancedStatusDiv.style.color = "#155724";
            advancedStatusDiv.innerHTML = `<strong>Success!</strong> EML files processed successfully.<br><br><strong>Command used:</strong> ${command}`;
        }
    });
});

// Assemble advanced section
newestFirstContainer.appendChild(newestFirstCheckbox);
newestFirstContainer.appendChild(newestFirstLabel);
dedupContainer.appendChild(dedupLabel);
dedupContainer.appendChild(dedupInput);

advancedSection.appendChild(advancedTitle);
advancedSection.appendChild(newestFirstContainer);
advancedSection.appendChild(dedupContainer);
advancedSection.appendChild(advancedButton);
advancedSection.appendChild(advancedStatusDiv);

dv.container.appendChild(advancedSection);
```

## How to Use

1. **Prepare your EML files**: Place all `.eml` files you want to convert in the `input` directory
2. **Click the button**: Use either the simple "Process EML Files" button or configure advanced options
3. **Wait for processing**: The button will show "Processing..." while the conversion runs
4. **Check results**: 
   - Converted Markdown files will be in the `output` directory
   - Processed EML files will be moved to the `done` directory
   - Status messages will appear below the button

## Requirements

- Python virtual environment at `Emails/eml2md/venv/`
- Required Python packages (email-validator, python-dateutil)
- Obsidian with DataViewJS enabled
- File system access permissions for running external commands

## Directory Structure

```
Emails/eml2md/
├── input/          # Place .eml files here
├── output/         # Converted .md files appear here
├── done/           # Processed .eml files are moved here
├── venv/           # Python virtual environment
│   └── Scripts/    # Contains python.exe
├── eml2md.py       # Main conversion script
└── email_reader_gui.md  # This file
```