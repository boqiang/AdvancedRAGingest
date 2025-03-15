"""
-----------------------------------------------------------------
(C) 2024 Prof. Tiran Dagan, FDU University. All rights reserved.
-----------------------------------------------------------------

Partition JSON Enrichment Module

This module provides functionality to enhance JSON data with LLM-generated
summaries of images using Ollama's vision model.
"""

import json
import os
import base64
import logging
import requests
from .config import global_config
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn


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
    
    # Check if we have a sample image to use when base64 data is missing
    sample_image_path = os.path.join("data", "input", "sample_image.jpg")
    has_sample_image = os.path.exists(sample_image_path)
    sample_image_base64 = None
    
    if has_sample_image:
        try:
            with open(sample_image_path, "rb") as image_file:
                sample_image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            console.print(f"Error reading sample image: {str(e)}", style="red")
            logging.error(f"Error reading sample image: {str(e)}")
    
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
            image_base64 = item['metadata'].get('image_base64')
            
            # If no base64 data but we have a sample image, use that instead
            if not image_base64 and sample_image_base64:
                image_base64 = sample_image_base64
            
            if image_base64:
                try:
                    summary = summarize_image_with_ollama(image_base64)
                    item['text'] = summary

                    # Save after each image is processed
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
                    progress.advance(task)
                except Exception as e:
                    console.print(f"Error processing image: {str(e)}", style="red")
                    logging.error(f"Error processing image: {str(e)}")
            else:
                console.print(f"Skipping image without base64 data: {item.get('text', 'Unnamed image')}", 
                            style="yellow")

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

def summarize_image_with_ollama(image_base64):
    """
    Generates a summary of an image using Ollama's vision model.

    Args:
        image_base64 (str): Base64-encoded image data.

    Returns:
        str: A text summary of the image content.
    """
    ollama_server = global_config.model.ollama_server
    model_name = global_config.model.llm_model
    
    # Construct the API endpoint URL
    api_url = f"{ollama_server}/api/chat"
    
    prompt = """You are an image summarizing agent. I will be giving you an image and you will provide a summary describing 
    the image, starting with "An image", or "An illustration", or "A diagram:", or "A logo:" or "A symbol:". If it contains a part, 
    you will try to identify the part and if it shows an action (such as a person cleaning 
    a pool or a woman holding a pool cleaning product) you will call those out. If it is a symbol, just give the symbol
    a meaningful name such as "warning symbol" or "attention!"
    """
    
    # Prepare the request payload
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [image_base64]
            }
        ],
        "stream": False
    }
    
    console.print(f"Sending request to Ollama server at {ollama_server}/api/chat")
    
    # Send the request to the Ollama server
    response = requests.post(api_url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        summary = result["message"]["content"]
        console.print(f"Successfully processed image using Ollama: {summary[:50]}...")
        return summary
    else:
        error_message = f"Error from Ollama server: {response.status_code} - {response.text}"
        console.print(error_message, style="red")
        logging.error(error_message)
        return "Error processing image with Ollama"