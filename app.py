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

app = FastAPI(title="EML to Markdown Converter GUI", version="1.0.0")

# Set up templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with Hello World interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/hello")
async def hello_api():
    """Simple API endpoint returning hello world."""
    return {"message": "Hello World from EML2MD FastAPI GUI!"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)