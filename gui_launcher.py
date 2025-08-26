#!/usr/bin/env python3
"""
GUI launcher for EML to Markdown converter.
Starts FastAPI server and opens a chromium-based window.
Terminates server when window is closed.
"""

import subprocess
import threading
import time
import sys
import os
import signal
import psutil
from pathlib import Path

class GUILauncher:
    def __init__(self):
        self.server_process = None
        self.browser_process = None
        self.running = True
        
    def find_chromium_browser(self):
        """Find available chromium-based browser."""
        browsers = [
            'google-chrome',
            'chromium-browser', 
            'chromium',
            'google-chrome-stable',
            'google-chrome-beta',
            'google-chrome-dev',
            'microsoft-edge',
            'brave-browser'
        ]
        
        for browser in browsers:
            try:
                subprocess.run([browser, '--version'], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL, 
                              check=True)
                return browser
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        return None

    def start_server(self):
        """Start FastAPI server in background."""
        print("Starting FastAPI server...")
        
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        app_path = script_dir / "app.py"
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, str(app_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(script_dir)
            )
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if server is running
            if self.server_process.poll() is None:
                print("FastAPI server started successfully on http://127.0.0.1:8000")
                return True
            else:
                print("Failed to start FastAPI server")
                return False
                
        except Exception as e:
            print(f"Error starting server: {e}")
            return False

    def open_browser(self):
        """Open chromium-based browser window."""
        browser = self.find_chromium_browser()
        
        if not browser:
            print("No chromium-based browser found. Please install Google Chrome, Chromium, or similar.")
            return False
            
        print(f"Opening browser: {browser}")
        
        try:
            # Browser arguments for app-like experience
            browser_args = [
                browser,
                '--app=http://127.0.0.1:8000',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-background-timer-throttling',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows'
            ]
            
            self.browser_process = subprocess.Popen(
                browser_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            print("Browser window opened")
            return True
            
        except Exception as e:
            print(f"Error opening browser: {e}")
            return False

    def monitor_browser(self):
        """Monitor browser process and terminate server when browser closes."""
        if not self.browser_process:
            return
            
        print("Monitoring browser window...")
        
        try:
            # Wait for browser process to end
            self.browser_process.wait()
            print("Browser window closed")
            
        except Exception as e:
            print(f"Error monitoring browser: {e}")
        
        finally:
            self.running = False
            self.cleanup()

    def cleanup(self):
        """Clean up processes."""
        print("Cleaning up...")
        
        # Terminate server process
        if self.server_process and self.server_process.poll() is None:
            try:
                print("Terminating FastAPI server...")
                self.server_process.terminate()
                
                # Wait a moment for graceful shutdown
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("Force killing server...")
                    self.server_process.kill()
                    
            except Exception as e:
                print(f"Error terminating server: {e}")
        
        # Ensure browser process is closed
        if self.browser_process and self.browser_process.poll() is None:
            try:
                self.browser_process.terminate()
            except Exception as e:
                print(f"Error terminating browser: {e}")

    def run(self):
        """Main launcher method."""
        print("EML to Markdown Converter GUI Launcher")
        print("=" * 40)
        
        # Start server
        if not self.start_server():
            print("Failed to start server. Exiting.")
            return 1
        
        # Open browser
        if not self.open_browser():
            print("Failed to open browser. Server is running at http://127.0.0.1:8000")
            self.cleanup()
            return 1
        
        # Monitor browser in separate thread
        monitor_thread = threading.Thread(target=self.monitor_browser, daemon=True)
        monitor_thread.start()
        
        try:
            # Keep main thread alive while browser is open
            while self.running and self.browser_process.poll() is None:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nShutdown requested...")
            self.running = False
            
        finally:
            self.cleanup()
            
        print("GUI application terminated.")
        return 0

def main():
    """Entry point for GUI launcher."""
    launcher = GUILauncher()
    
    # Handle cleanup on exit
    def signal_handler(signum, frame):
        print("\nReceived signal, shutting down...")
        launcher.running = False
        launcher.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    return launcher.run()

if __name__ == "__main__":
    sys.exit(main())