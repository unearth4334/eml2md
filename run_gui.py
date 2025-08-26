#!/usr/bin/env python3
"""
Simple entry point script for the FastAPI GUI.
Run this to launch the GUI application.
Supports --verbose flag for detailed logging.
"""

import sys
import argparse
from gui_launcher import main

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Launch EML to Markdown GUI application')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging for debugging')
    parser.add_argument('--tkinter', '-t', action='store_true',
                        help='Force use of native Tkinter GUI (skip web-based GUI)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    sys.exit(main(verbose=args.verbose, force_tkinter=args.tkinter))