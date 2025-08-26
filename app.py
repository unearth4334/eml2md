#!/usr/bin/env python3
"""
FastAPI GUI application for EML to Markdown converter.
Provides a web interface with Hello World starting point.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import socket
import sys

app = FastAPI(title="EML to Markdown Converter GUI", version="1.0.0")

# Set up templates
templates = Jinja2Templates(directory="templates")

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with Hello World interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/hello")
async def hello_api():
    """Simple API endpoint returning hello world."""
    return {"message": "Hello World from EML2MD FastAPI GUI!"}

if __name__ == "__main__":
    # Get port from command line argument or find available port
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port argument: {sys.argv[1]}")
            sys.exit(1)
    else:
        # Find available port starting from 8000
        available_port = find_available_port(8000)
        if available_port is None:
            print("ERROR: No available ports found in range 8000-8009")
            sys.exit(1)
        port = available_port
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=port)
    except OSError as e:
        print(f"ERROR: {e}")
        print(f"Failed to bind to port {port}. Please try a different port or check if another application is using this port.")
        sys.exit(1)