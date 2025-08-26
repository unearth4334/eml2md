#!/usr/bin/env python3
"""
GUI launcher for EML to Markdown converter.
Tries FastAPI server approach first, falls back to Tkinter if socket binding fails.
"""

import subprocess
import threading
import time
import sys
import os
import signal
import psutil
from pathlib import Path
import socket

class GUILauncher:
    def __init__(self, verbose=False, force_tkinter=False):
        self.server_process = None
        self.browser_process = None
        self.running = True
        self.verbose = verbose
        self.force_tkinter = force_tkinter
        
    def log(self, message):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[VERBOSE] {message}")

    def check_port_available(self, port=8000):
        """Check if port is available for binding."""
        try:
            self.log(f"Checking if port {port} is available...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                self.log(f"Port {port} is available")
                return True
        except OSError as e:
            self.log(f"Port {port} is not available: {e}")
            return False

    def start_tkinter_gui(self):
        """Start Tkinter-based GUI as fallback."""
        print("Starting Tkinter-based GUI...")
        self.log("Attempting to start Tkinter GUI")
        
        try:
            from gui_tkinter import main as tkinter_main
            self.log("Successfully imported Tkinter GUI module")
            print("Launching native desktop interface...")
            return tkinter_main()
        except ImportError as e:
            print(f"Error importing Tkinter GUI: {e}")
            self.log(f"Failed to import Tkinter GUI: {e}")
            return 1
        except Exception as e:
            print(f"Error starting Tkinter GUI: {e}")
            self.log(f"Failed to start Tkinter GUI: {e}")
            return 1
        """Find available chromium-based browser."""
        self.log("Searching for chromium-based browsers...")
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
            self.log(f"Checking for browser: {browser}")
            try:
                subprocess.run([browser, '--version'], 
                              stdout=subprocess.DEVNULL, 
                              stderr=subprocess.DEVNULL, 
                              check=True)
                self.log(f"Found browser: {browser}")
                return browser
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.log(f"Browser not found: {browser}")
                continue
        
        self.log("No chromium-based browser found")
        return None

    def start_server(self):
        """Start FastAPI server in background."""
        print("Starting FastAPI server...")
        
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        app_path = script_dir / "app.py"
        
        self.log(f"Script directory: {script_dir}")
        self.log(f"App path: {app_path}")
        
        # Check if app.py exists
        if not app_path.exists():
            print(f"ERROR: FastAPI app not found at {app_path}")
            return False
        
        self.log(f"Starting server with command: {sys.executable} {app_path}")
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, str(app_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(script_dir),
                text=True  # Ensure text mode for easier reading
            )
            
            self.log("Server process started, waiting for startup...")
            
            # Wait a moment for server to start
            time.sleep(2)
            
            # Check if server is running
            if self.server_process.poll() is None:
                print("FastAPI server started successfully on http://127.0.0.1:8000")
                self.log("Server startup completed successfully")
                return True
            else:
                # Server process has terminated, get the error output
                stdout, stderr = self.server_process.communicate()
                exit_code = self.server_process.returncode
                
                print("Failed to start FastAPI server")
                print(f"Server process exited with code: {exit_code}")
                
                if stderr:
                    print("Error output:")
                    print(stderr)
                
                if stdout:
                    print("Standard output:")
                    print(stdout)
                
                return False
                
        except Exception as e:
            print(f"Error starting server: {e}")
            self.log(f"Exception details: {type(e).__name__}: {e}")
            return False

    def open_browser(self):
        """Open chromium-based browser window."""
        self.log("Starting browser search and launch process...")
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
            
            self.log(f"Browser command: {' '.join(browser_args)}")
            
            self.browser_process = subprocess.Popen(
                browser_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            print("Browser window opened")
            self.log(f"Browser process PID: {self.browser_process.pid}")
            return True
            
        except Exception as e:
            print(f"Error opening browser: {e}")
            self.log(f"Browser exception details: {type(e).__name__}: {e}")
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
        self.log("Starting cleanup process...")
        
        # Terminate server process
        if self.server_process and self.server_process.poll() is None:
            try:
                print("Terminating FastAPI server...")
                self.log(f"Terminating server process PID: {self.server_process.pid}")
                self.server_process.terminate()
                
                # Wait a moment for graceful shutdown
                try:
                    self.server_process.wait(timeout=5)
                    self.log("Server terminated gracefully")
                except subprocess.TimeoutExpired:
                    print("Force killing server...")
                    self.log("Server did not terminate gracefully, force killing...")
                    self.server_process.kill()
                    self.log("Server force killed")
                    
            except Exception as e:
                print(f"Error terminating server: {e}")
                self.log(f"Server termination exception: {type(e).__name__}: {e}")
        else:
            self.log("Server process already terminated or not started")
        
        # Ensure browser process is closed
        if self.browser_process and self.browser_process.poll() is None:
            try:
                self.log(f"Terminating browser process PID: {self.browser_process.pid}")
                self.browser_process.terminate()
                self.log("Browser process terminated")
            except Exception as e:
                print(f"Error terminating browser: {e}")
                self.log(f"Browser termination exception: {type(e).__name__}: {e}")
        else:
            self.log("Browser process already terminated or not started")
        
        self.log("Cleanup process completed")

    def run(self):
        """Main launcher method with fallback logic."""
        print("EML to Markdown Converter GUI Launcher")
        print("=" * 40)
        
        # If force_tkinter is set, skip web-based GUI
        if self.force_tkinter:
            print("Using native Tkinter GUI (forced)")
            return self.start_tkinter_gui()
        
        # Check if port is available
        if not self.check_port_available():
            print("Port 8000 is not available, falling back to native GUI...")
            return self.start_tkinter_gui()
        
        # Try web-based GUI first
        print("Attempting to start web-based GUI...")
        
        # Start server
        if not self.start_server():
            print("Failed to start server. Falling back to native GUI...")
            return self.start_tkinter_gui()
        
        # Open browser
        if not self.open_browser():
            print("Failed to open browser. Falling back to native GUI...")
            self.cleanup()
            return self.start_tkinter_gui()
        
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

def main(verbose=False, force_tkinter=False):
    """Entry point for GUI launcher."""
    launcher = GUILauncher(verbose=verbose, force_tkinter=force_tkinter)
    
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