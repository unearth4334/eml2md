#!/usr/bin/env python3
"""
EML to Markdown Converter GUI Launcher
A FastAPI-based web interface for converting EML files to Markdown.
"""

import os
import sys
import socket
import subprocess
import time
import webbrowser
from pathlib import Path
import tempfile
import shutil
from typing import List

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
except ImportError:
    print("FastAPI dependencies not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "python-multipart"])
    from fastapi import FastAPI, File, UploadFile, HTTPException
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn

# Import the existing eml2md module
from eml2md import process_eml_file

app = FastAPI(title="EML to Markdown Converter", description="Convert EML files to Markdown format")

def find_available_port(start_port=8000, max_attempts=50):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

@app.get("/", response_class=HTMLResponse)
async def main():
    """Main page with file upload form"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EML to Markdown Converter</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                transition: border-color 0.3s;
            }
            .upload-area:hover {
                border-color: #007bff;
            }
            input[type="file"] {
                margin: 20px 0;
            }
            button {
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background-color: #0056b3;
            }
            .options {
                margin: 20px 0;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            .checkbox-group {
                margin: 10px 0;
            }
            label {
                margin-left: 8px;
            }
            .result {
                margin-top: 20px;
                padding: 20px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 5px;
                display: none;
            }
            .error {
                margin-top: 20px;
                padding: 20px;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 5px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔄 EML to Markdown Converter</h1>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area">
                    <h3>Select EML File(s)</h3>
                    <input type="file" id="files" name="files" multiple accept=".eml" required>
                    <p>Drag and drop EML files here or click to browse</p>
                </div>
                
                <div class="options">
                    <h4>Conversion Options:</h4>
                    <div class="checkbox-group">
                        <input type="checkbox" id="newest_first" name="newest_first">
                        <label for="newest_first">Sort emails newest first (default: oldest first)</label>
                    </div>
                    <div class="checkbox-group">
                        <label for="dedup_threshold">Deduplication threshold (1-20):</label>
                        <input type="number" id="dedup_threshold" name="dedup_threshold" value="8" min="1" max="20">
                    </div>
                </div>
                
                <button type="submit">Convert to Markdown</button>
            </form>
            
            <div id="result" class="result"></div>
            <div id="error" class="error"></div>
        </div>

        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                const files = document.getElementById('files').files;
                const newestFirst = document.getElementById('newest_first').checked;
                const dedupThreshold = document.getElementById('dedup_threshold').value;
                
                if (files.length === 0) {
                    showError('Please select at least one EML file');
                    return;
                }
                
                for (let file of files) {
                    formData.append('files', file);
                }
                formData.append('newest_first', newestFirst);
                formData.append('dedup_threshold', dedupThreshold);
                
                try {
                    showMessage('Converting files, please wait...');
                    const response = await fetch('/convert', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        showResult(result);
                    } else {
                        const error = await response.text();
                        showError(`Conversion failed: ${error}`);
                    }
                } catch (error) {
                    showError(`Error: ${error.message}`);
                }
            });
            
            function showResult(result) {
                const resultDiv = document.getElementById('result');
                const errorDiv = document.getElementById('error');
                
                resultDiv.innerHTML = `
                    <h4>✅ Conversion Successful!</h4>
                    <p><strong>Files processed:</strong> ${result.files_processed}</p>
                    <p><strong>Output files:</strong></p>
                    <ul>
                        ${result.output_files.map(file => `<li><a href="/download/${encodeURIComponent(file)}" target="_blank">${file}</a></li>`).join('')}
                    </ul>
                `;
                resultDiv.style.display = 'block';
                errorDiv.style.display = 'none';
            }
            
            function showError(message) {
                const errorDiv = document.getElementById('error');
                const resultDiv = document.getElementById('result');
                
                errorDiv.innerHTML = `<h4>❌ Error</h4><p>${message}</p>`;
                errorDiv.style.display = 'block';
                resultDiv.style.display = 'none';
            }
            
            function showMessage(message) {
                const resultDiv = document.getElementById('result');
                const errorDiv = document.getElementById('error');
                
                resultDiv.innerHTML = `<h4>⏳ Processing</h4><p>${message}</p>`;
                resultDiv.style.display = 'block';
                errorDiv.style.display = 'none';
            }
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/convert")
async def convert_files(
    files: List[UploadFile] = File(...),
    newest_first: bool = False,
    dedup_threshold: int = 8
):
    """Convert uploaded EML files to Markdown"""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    output_files = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create input directory in temp folder
        input_dir = os.path.join(temp_dir, "input")
        os.makedirs(input_dir, exist_ok=True)
        
        # Save uploaded files
        for file in files:
            if not file.filename.lower().endswith('.eml'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not an EML file")
            
            file_path = os.path.join(input_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
        
        # Process each EML file
        for file in files:
            eml_path = os.path.join(input_dir, file.filename)
            try:
                md_path = process_eml_file(eml_path, newest_first)
                if md_path and os.path.exists(md_path):
                    # Copy to a accessible location
                    output_filename = os.path.basename(md_path)
                    output_path = os.path.join("output", output_filename)
                    os.makedirs("output", exist_ok=True)
                    shutil.copy2(md_path, output_path)
                    output_files.append(output_filename)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error processing {file.filename}: {str(e)}")
        
        return {
            "status": "success",
            "files_processed": len(files),
            "output_files": output_files
        }
    
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download converted markdown file"""
    file_path = os.path.join("output", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/markdown'
    )

def start_server():
    """Start the FastAPI server with proper error handling"""
    print("EML to Markdown Converter GUI Launcher")
    print("=" * 40)
    
    try:
        # Find an available port
        port = find_available_port(start_port=8000)
        print(f"Starting FastAPI server on port {port}...")
        
        # Start the server
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=port,
            log_level="info",
            access_log=False
        )
        server = uvicorn.Server(config)
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(1.5)
            webbrowser.open(f"http://127.0.0.1:{port}")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        print(f"Server starting at http://127.0.0.1:{port}")
        print("Opening web browser...")
        print("Press Ctrl+C to stop the server")
        
        server.run()
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Failed to start server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(start_server())