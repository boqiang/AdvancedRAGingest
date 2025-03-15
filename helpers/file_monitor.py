"""
-----------------------------------------------------------------
(C) 2024 Prof. Tiran Dagan, FDU University. All rights reserved.
-----------------------------------------------------------------

File Monitoring Module

This module provides functionality to monitor a directory for new files
and trigger processing when new files are detected.
"""

import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console

from .config import global_config
from .file_and_folder import get_files_with_extension
from .pdf_ingest import PDFProcessor
from .generate_markdown import create_debugging_markdown

console = Console()

class FileHandler(FileSystemEventHandler):
    """
    Handler for file system events.
    """
    def __init__(self, processor):
        """
        Initialize the file handler.
        
        Args:
            processor (PDFProcessor): The PDF processor to use for processing files.
        """
        self.processor = processor
        self.processed_files = set()
        
    def on_created(self, event):
        """
        Handle file creation events.
        
        Args:
            event (FileSystemEvent): The file system event.
        """
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            
            # Check if we've already processed this file
            if file_path in self.processed_files:
                return
                
            console.print(f"New PDF detected: {file_name}", style="green")
            
            # Process the PDF
            self.process_file(file_path)
            
            # Add to processed files
            self.processed_files.add(file_path)
    
    def process_file(self, file_path):
        """
        Process a single PDF file.
        
        Args:
            file_path (str): Path to the PDF file.
        """
        try:
            # Get the directory of the file
            input_dir = os.path.dirname(file_path)
            
            # Process the PDF
            self.processor.process_pdfs(input_dir, [file_path])
            
            # Create debugging markdown
            create_debugging_markdown()
            
            console.print(f"Successfully processed {os.path.basename(file_path)}", style="green")
        except Exception as e:
            console.print(f"Error processing {os.path.basename(file_path)}: {str(e)}", style="red")
            logging.error(f"Error processing {file_path}: {str(e)}")

class FileMonitor:
    """
    Monitor a directory for new files.
    """
    def __init__(self, directory):
        """
        Initialize the file monitor.
        
        Args:
            directory (str): The directory to monitor.
        """
        self.directory = directory
        self.processor = PDFProcessor()
        self.event_handler = FileHandler(self.processor)
        self.observer = Observer()
        
    def start(self):
        """
        Start monitoring the directory.
        """
        # Process existing files first
        self.process_existing_files()
        
        # Start monitoring for new files
        self.observer.schedule(self.event_handler, self.directory, recursive=False)
        self.observer.start()
        
        try:
            console.print(f"Monitoring directory: {self.directory}", style="blue")
            console.print("Press Ctrl+C to stop monitoring", style="yellow")
            
            while True:
                time.sleep(int(global_config.file_monitoring.polling_interval))
        except KeyboardInterrupt:
            self.observer.stop()
        
        self.observer.join()
        
    def process_existing_files(self):
        """
        Process existing PDF files in the directory.
        """
        pdf_files = get_files_with_extension(self.directory, '.pdf')
        
        if pdf_files:
            console.print(f"Processing {len(pdf_files)} existing PDF files...", style="blue")
            
            for file_path in pdf_files:
                full_path = os.path.join(self.directory, file_path)
                self.event_handler.processed_files.add(full_path)
                self.event_handler.process_file(full_path) 