"""
-----------------------------------------------------------------
(C) 2024 Prof. Tiran Dagan, FDU University. All rights reserved.
-----------------------------------------------------------------

PDF Ingestion and Processing Application

This script provides an automated system for processing PDF files.
It monitors the input directory for new PDF files and automatically
processes them, extracting annotations and generating debugging markdown.

Key features:
- Automatic monitoring of input directory
- Processing of new PDF files as they are added
- Error handling and logging

Usage:
python main.py
"""

import os

from helpers import *
from helpers.pdf_ingest import PDFProcessor
from helpers.logging import setup_logging
from helpers.generate_markdown import create_debugging_markdown
from helpers.file_monitor import FileMonitor

from rich.console import Console

console = Console()

def main():
    """Main function to run the PDF processing application."""
    console.print("PDF Processing Application", style="bold blue")
    console.print("-" * 50)
    
    setup_logging()
    load_config()
    
    # Get the input directory from the configuration
    input_dir = global_config.directories.input_dir
    
    # Create a file monitor for the input directory
    monitor = FileMonitor(input_dir)
    
    # Start monitoring the directory
    monitor.start()
    
    console.print("\nApplication completed.", style="green")

if __name__ == "__main__":
    main()
