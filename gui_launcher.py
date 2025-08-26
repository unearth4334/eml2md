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
import socket
from pathlib import Path

class GUILauncher:
    def __init__(self, verbose=False):
        self.server_process = None
        self.browser_process = None
        self.running = True
        self.verbose = verbose
        self.port = None
        
    def log(self, message):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[VERBOSE] {message}")

    def find_available_port(self, start_port=8000, max_attempts=10):
        """Find an available port starting from start_port."""
        self.log(f"Searching for available port starting from {start_port}")
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.bind(('127.0.0.1', port))
                    self.log(f"Port {port} is available")
                    return port
            except OSError:
                self.log(f"Port {port} is not available")
                continue
        self.log(f"No available ports found in range {start_port}-{start_port + max_attempts - 1}")
        return None

    def find_chromium_browser(self):
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
        
        # Find available port
        if self.port is None:
            self.port = self.find_available_port(8000)
            if self.port is None:
                print("ERROR: No available ports found in range 8000-8009")
                return False
        
        print(f"Using port: {self.port}")
        
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        app_path = script_dir / "app.py"
        
        self.log(f"Script directory: {script_dir}")
        self.log(f"App path: {app_path}")
        
        # Check if app.py exists
        if not app_path.exists():
            print(f"ERROR: FastAPI app not found at {app_path}")
            return False
        
        self.log(f"Starting server with command: {sys.executable} {app_path} {self.port}")
        
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, str(app_path), str(self.port)],
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
                print(f"FastAPI server started successfully on http://127.0.0.1:{self.port}")
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
        if self.port is None:
            print("ERROR: Port not set, cannot open browser")
            return False
            
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
                f'--app=http://127.0.0.1:{self.port}',
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
        """Main launcher method."""
        print("EML to Markdown Converter GUI Launcher")
        print("=" * 40)
        
        # Start server
        if not self.start_server():
            print("Failed to start server. Exiting.")
            return 1
        
        # Open browser
        if not self.open_browser():
            print(f"Failed to open browser. Server is running at http://127.0.0.1:{self.port}")
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

def main(verbose=False):
    """Entry point for GUI launcher."""
    launcher = GUILauncher(verbose=verbose)
    
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