"""
-----------------------------------------------------------------
(C) 2024 Prof. Tiran Dagan, FDU University. All rights reserved.
-----------------------------------------------------------------

Partition JSON Enrichment Module

This module provides functionality to enhance JSON data with LLM-generated
summaries of images using Ollama models.
"""

import json
import requests
import base64
import os
from .config import global_config
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from PIL import Image
from io import BytesIO

console = Console()

def enrich_json_with_summaries(json_file):
    """
    Processes JSON data, generating summaries for images that don't have them.
    
    Args:
        json_file (str): Path to the JSON file being processed.
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # Retrieve lists of items to enrich
    # See element types in document elements: https://docs.unstructured.io/api-reference/api-services/document-elements
    
    imageElements = [item for item in json_data if item['type'] == 'Image']
    tableElements = [item for item in json_data if item['type'] == 'Table']
    textElements = [item for item in json_data if item['type'] == 'NarrativeText']
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True
    ) as progress:
        
        # Images
        task = progress.add_task(
            f"Enriching images", 
            total=len(imageElements)
        )

        for idx, item in enumerate(imageElements, 1):
            progress.update(task, description=f"Enriching images: {idx}/{len(imageElements)}")
            
            # Try to use the sample image we created earlier
            if os.path.exists("data/input/sample_image.jpg"):
                try:
                    # Read the image file and convert to base64
                    with open("data/input/sample_image.jpg", "rb") as img_file:
                        image_data = img_file.read()
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                    
                    summary = summarize_image(image_base64)
                    item['text'] = summary

                    # Save after each image is processed
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
                    progress.advance(task)
                    console.print(f"Successfully processed image using Ollama: {summary[:50]}...", style="green")
                except Exception as e:
                    console.print(f"Error processing image: {str(e)}", style="red")
                    logging.error(f"Error processing image: {str(e)}")
            else:
                console.print(f"Sample image not found at data/input/sample_image.jpg", style="yellow")

        # Tables
        # To Do
        task = progress.add_task(
            f"Processing tables", 
            total=len(tableElements)
        )

        for item in tableElements:
            # To Do
            pass

        # Text
        # To Do
        task = progress.add_task(
            f"Processing text", 
            total=len(textElements)
        )

        for item in textElements:
            # To Do
            pass

    return

def summarize_image(image_base64):
    """
    Generates a summary of an image using Ollama's llama3.2-vision model.

    Args:
        image_base64 (str): Base64-encoded image data.

    Returns:
        str: A text summary of the image content.
    """
    ollama_url = f"{global_config.model.ollama_server}/api/chat"
    model = global_config.model.llm_model
    
    prompt = """You are an image summarizing agent. I will be giving you an image and you will provide a summary describing 
    the image, starting with "An image", or "An illustration", or "A diagram:", or "A logo:" or "A symbol:". If it contains a part, 
    you will try to identify the part and if it shows an action (such as a person cleaning 
    a pool or a woman holding a pool cleaning product) you will call those out. If it is a symbol, just give the symbol
    a meaningful name such as "warning symbol" or "attention!"
    """
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [image_base64]
            }
        ],
        "stream": False
    }
    
    try:
        console.print(f"Sending request to Ollama server at {ollama_url}", style="blue")
        response = requests.post(ollama_url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result["message"]["content"]
        else:
            error_msg = f"Error from Ollama API: {response.status_code} - {response.text}"
            logging.error(error_msg)
            raise Exception(error_msg)
    except Exception as e:
        logging.error(f"Error communicating with Ollama server: {str(e)}")
        raise Exception(f"Failed to get image summary: {str(e)}")