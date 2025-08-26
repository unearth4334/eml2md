#!/usr/bin/env python3
"""
Tkinter-based GUI for EML to Markdown converter.
Provides a native desktop interface without requiring network sockets.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import subprocess
import sys
from pathlib import Path


class EMLConverterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EML to Markdown Converter")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Variables
        self.input_dir = tk.StringVar(value="input")
        self.output_dir = tk.StringVar(value="output")
        self.newest_first = tk.BooleanVar(value=False)
        self.dedup_threshold = tk.IntVar(value=8)
        
        self.setup_ui()
        self.center_window()
        
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="EML to Markdown Converter", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input directory selection
        ttk.Label(main_frame, text="Input Directory:").grid(row=1, column=0, sticky=tk.W, pady=5)
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(input_frame, textvariable=self.input_dir, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(input_frame, text="Browse", command=self.browse_input_dir).grid(row=0, column=1)
        
        # Output directory selection
        ttk.Label(main_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_frame, text="Browse", command=self.browse_output_dir).grid(row=0, column=1)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        options_frame.columnconfigure(1, weight=1)
        
        # Newest first option
        ttk.Checkbutton(options_frame, text="Sort emails newest first (default: oldest first)", 
                       variable=self.newest_first).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Deduplication threshold
        ttk.Label(options_frame, text="Deduplication Threshold:").grid(row=1, column=0, sticky=tk.W, pady=5)
        threshold_frame = ttk.Frame(options_frame)
        threshold_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Scale(threshold_frame, from_=1, to=20, variable=self.dedup_threshold, 
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Label(threshold_frame, textvariable=self.dedup_threshold).grid(row=0, column=1, padx=(10, 0))
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Create Directories", 
                  command=self.create_directories).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Convert EML Files", 
                  command=self.convert_files).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Read MD Emails", 
                  command=self.read_md_emails).grid(row=0, column=2, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Output text area
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="5")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, wrap=tk.WORD)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def browse_input_dir(self):
        """Browse for input directory."""
        directory = filedialog.askdirectory(title="Select Input Directory", 
                                           initialdir=self.input_dir.get())
        if directory:
            self.input_dir.set(directory)
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory", 
                                           initialdir=self.output_dir.get())
        if directory:
            self.output_dir.set(directory)
    
    def log_output(self, message):
        """Add message to output text area."""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()
    
    def create_directories(self):
        """Create required directories."""
        try:
            self.status_var.set("Creating directories...")
            self.log_output("Creating directories...")
            
            directories = [self.input_dir.get(), self.output_dir.get(), "done"]
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
                self.log_output(f"Created directory: {directory}")
            
            self.status_var.set("Directories created successfully")
            self.log_output("All directories created successfully!")
            
        except Exception as e:
            self.status_var.set("Error creating directories")
            self.log_output(f"Error creating directories: {str(e)}")
            messagebox.showerror("Error", f"Failed to create directories: {str(e)}")
    
    def convert_files(self):
        """Convert EML files to Markdown."""
        def run_conversion():
            try:
                self.progress.start()
                self.status_var.set("Converting EML files...")
                self.log_output("Starting EML to Markdown conversion...")
                
                # Build command
                cmd = [sys.executable, "eml2md.py"]
                if self.newest_first.get():
                    cmd.append("--newest-first")
                cmd.extend(["--dedup-threshold", str(self.dedup_threshold.get())])
                
                self.log_output(f"Running command: {' '.join(cmd)}")
                
                # Run the conversion
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
                
                if result.returncode == 0:
                    self.log_output("Conversion completed successfully!")
                    self.log_output("--- Standard Output ---")
                    self.log_output(result.stdout)
                    self.status_var.set("Conversion completed successfully")
                else:
                    self.log_output("Conversion failed!")
                    self.log_output("--- Error Output ---")
                    self.log_output(result.stderr)
                    self.status_var.set("Conversion failed")
                
            except Exception as e:
                self.log_output(f"Error running conversion: {str(e)}")
                self.status_var.set("Error during conversion")
                messagebox.showerror("Error", f"Failed to run conversion: {str(e)}")
            finally:
                self.progress.stop()
        
        # Run in separate thread to prevent GUI freezing
        threading.Thread(target=run_conversion, daemon=True).start()
    
    def read_md_emails(self):
        """Launch the Markdown email reader."""
        try:
            self.status_var.set("Launching MD email reader...")
            self.log_output("Launching Markdown email reader...")
            
            # Run the read_md_email.py script
            subprocess.Popen([sys.executable, "read_md_email.py"], cwd=os.getcwd())
            
            self.log_output("MD email reader launched successfully!")
            self.status_var.set("MD email reader launched")
            
        except Exception as e:
            self.log_output(f"Error launching MD email reader: {str(e)}")
            self.status_var.set("Error launching MD reader")
            messagebox.showerror("Error", f"Failed to launch MD email reader: {str(e)}")
    
    def run(self):
        """Start the GUI application."""
        self.status_var.set("Ready - Select directories and options, then convert EML files")
        self.log_output("EML to Markdown Converter GUI started")
        self.log_output("1. Set input/output directories")
        self.log_output("2. Adjust options if needed")
        self.log_output("3. Create directories if they don't exist")
        self.log_output("4. Convert EML files")
        self.log_output("")
        
        self.root.mainloop()


def main():
    """Entry point for Tkinter GUI."""
    try:
        app = EMLConverterGUI()
        app.run()
        return 0
    except Exception as e:
        print(f"Error starting Tkinter GUI: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())