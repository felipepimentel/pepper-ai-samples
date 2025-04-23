#!/usr/bin/env python
"""
Client for the A2A Web Integration Agent

This script provides functions for interacting with the Web Integration Agent and
running demos of its capabilities.
"""

import argparse
import asyncio
import base64
import json
import mimetypes
import os
import sys
import uuid
from typing import Dict, List, Optional, Any, Union

import httpx
from pydantic import BaseModel

# Configuration
BASE_URL = "http://localhost:8002"
HEADERS = {"Content-Type": "application/json"}

# Models for request/response structures
class Message(BaseModel):
    role: str
    content: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    messages: List[Message]

class UploadResponse(BaseModel):
    task_id: str
    file_id: str
    filename: str
    success: bool

class FormField(BaseModel):
    id: str
    label: str
    type: str
    required: bool = False
    options: Optional[List[Dict[str, str]]] = None

class Form(BaseModel):
    id: str
    title: str
    description: str
    fields: List[FormField]

# Helper functions
async def create_http_client() -> httpx.AsyncClient:
    """Create an HTTP client with appropriate timeout settings."""
    return httpx.AsyncClient(timeout=30.0)

async def fetch_agent_card() -> Dict[str, Any]:
    """Fetch the agent card (metadata) from the server."""
    async with await create_http_client() as client:
        response = await client.get(f"{BASE_URL}/.well-known/agent.json")
        response.raise_for_status()
        return response.json()

async def create_task() -> str:
    """Create a new task and return the task ID."""
    async with await create_http_client() as client:
        response = await client.post(f"{BASE_URL}/tasks")
        response.raise_for_status()
        data = response.json()
        return data["task_id"]

async def get_task(task_id: str) -> TaskResponse:
    """Get the current state of a task."""
    async with await create_http_client() as client:
        response = await client.get(f"{BASE_URL}/tasks/{task_id}")
        response.raise_for_status()
        return TaskResponse(**response.json())

async def send_message(task_id: str, message: str) -> TaskResponse:
    """Send a message to a task and return the updated task state."""
    async with await create_http_client() as client:
        response = await client.post(
            f"{BASE_URL}/tasks/{task_id}/send",
            json={"message": message}
        )
        response.raise_for_status()
        return TaskResponse(**response.json())

async def upload_file(task_id: str, file_path: str, description: str = "") -> UploadResponse:
    """Upload a file to a task."""
    # Determine file type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    # Read file content
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # Encode file content
    encoded_content = base64.b64encode(file_content).decode("utf-8")
    
    # Prepare upload data
    upload_data = {
        "filename": os.path.basename(file_path),
        "mime_type": mime_type,
        "content": encoded_content,
        "description": description
    }
    
    # Send request
    async with await create_http_client() as client:
        response = await client.post(
            f"{BASE_URL}/tasks/{task_id}/upload",
            json=upload_data
        )
        response.raise_for_status()
        return UploadResponse(**response.json())

async def submit_form(task_id: str, form_data: Dict[str, Any]) -> TaskResponse:
    """Submit form data to a task."""
    async with await create_http_client() as client:
        response = await client.post(
            f"{BASE_URL}/tasks/{task_id}/form",
            json={"form_data": form_data}
        )
        response.raise_for_status()
        return TaskResponse(**response.json())

# Demo scenarios
async def demo_web_search() -> None:
    """Demonstrate the web search capability."""
    print("Demonstrating Web Search Capability")
    print("-" * 40)
    
    # Create a new task
    task_id = await create_task()
    print(f"Task created: {task_id}")
    
    # Ask a search question
    query = "What is the A2A protocol and how does it relate to AI agents?"
    print(f"Sending search query: {query}")
    
    response = await send_message(task_id, query)
    
    # Print the response
    print("\nAgent Response:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    print("-" * 40)
    return task_id

async def demo_image_generation() -> None:
    """Demonstrate the image generation capability."""
    print("Demonstrating Image Generation Capability")
    print("-" * 40)
    
    # Create a new task
    task_id = await create_task()
    print(f"Task created: {task_id}")
    
    # Request an image
    prompt = "Generate an image of a beautiful sunset over mountains with a lake in the foreground"
    print(f"Sending image generation prompt: {prompt}")
    
    response = await send_message(task_id, prompt)
    
    # Print the response
    print("\nAgent Response:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    print("-" * 40)
    return task_id

async def demo_image_analysis(image_path: str) -> None:
    """Demonstrate the image analysis capability."""
    print("Demonstrating Image Analysis Capability")
    print("-" * 40)
    
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        return
    
    # Create a new task
    task_id = await create_task()
    print(f"Task created: {task_id}")
    
    # Upload the image
    print(f"Uploading image: {image_path}")
    upload_result = await upload_file(
        task_id, 
        image_path, 
        "Please analyze this image and tell me what you see."
    )
    print(f"File uploaded: {upload_result.file_id}")
    
    # Wait for response
    response = await get_task(task_id)
    
    # Print the response
    print("\nAgent Response:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    print("-" * 40)
    return task_id

async def demo_receipt_processing(receipt_path: str) -> None:
    """Demonstrate the receipt processing capability."""
    print("Demonstrating Receipt Processing Capability")
    print("-" * 40)
    
    if not os.path.exists(receipt_path):
        print(f"Error: Receipt file not found: {receipt_path}")
        return
    
    # Create a new task
    task_id = await create_task()
    print(f"Task created: {task_id}")
    
    # Upload the receipt
    print(f"Uploading receipt: {receipt_path}")
    upload_result = await upload_file(
        task_id, 
        receipt_path, 
        "Please extract the information from this receipt."
    )
    print(f"File uploaded: {upload_result.file_id}")
    
    # Wait for response
    response = await get_task(task_id)
    
    # Print the response
    print("\nAgent Response:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    print("-" * 40)
    return task_id

async def demo_currency_conversion() -> None:
    """Demonstrate the currency conversion capability."""
    print("Demonstrating Currency Conversion Capability")
    print("-" * 40)
    
    # Create a new task
    task_id = await create_task()
    print(f"Task created: {task_id}")
    
    # Request currency conversion
    query = "Please convert 100 USD to EUR, JPY, and GBP."
    print(f"Sending conversion request: {query}")
    
    response = await send_message(task_id, query)
    
    # Print the response
    print("\nAgent Response:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    print("-" * 40)
    return task_id

async def demo_data_visualization() -> None:
    """Demonstrate the data visualization capability."""
    print("Demonstrating Data Visualization Capability")
    print("-" * 40)
    
    # Create a new task
    task_id = await create_task()
    print(f"Task created: {task_id}")
    
    # Send data visualization request
    query = "Please create a visualization of the following quarterly revenue data: Q1: 84, Q2: 93, Q3: 65, Q4: 120"
    print(f"Sending visualization request: {query}")
    
    response = await send_message(task_id, query)
    
    # Print the response
    print("\nAgent Response:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    print("-" * 40)
    return task_id

async def demo_form_submission() -> None:
    """Demonstrate the form submission capability."""
    print("Demonstrating Form Submission Capability")
    print("-" * 40)
    
    # Create a new task
    task_id = await create_task()
    print(f"Task created: {task_id}")
    
    # Request a form
    print("Requesting a form")
    response = await send_message(task_id, "I need to file an expense report")
    
    # Print the form description
    print("\nForm request received:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    # Create sample form data
    form_data = {
        "expense_type": "Travel",
        "amount": 123.45,
        "date": "2023-10-15",
        "description": "Business trip to client office",
        "currency": "USD"
    }
    
    print(f"\nSubmitting form data: {json.dumps(form_data, indent=2)}")
    
    # Submit the form
    response = await submit_form(task_id, form_data)
    
    # Print the response
    print("\nForm submission response:")
    for message in response.messages:
        if message.role == "assistant":
            print(f"{message.content}")
    
    print("-" * 40)
    return task_id

async def demo_all(image_path: str, receipt_path: str) -> None:
    """Run all demos sequentially."""
    print("Running All Demos")
    print("=" * 50)
    
    await demo_web_search()
    await demo_image_generation()
    
    if image_path and os.path.exists(image_path):
        await demo_image_analysis(image_path)
    else:
        print("Skipping image analysis demo: no valid image provided")
    
    if receipt_path and os.path.exists(receipt_path):
        await demo_receipt_processing(receipt_path)
    else:
        print("Skipping receipt processing demo: no valid receipt provided")
    
    await demo_currency_conversion()
    await demo_data_visualization()
    await demo_form_submission()
    
    print("\nAll demos completed!")

# Command-line interface
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="A2A Web Integration Client")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Agent card command
    subparsers.add_parser("agent_card", help="Get the agent card (metadata)")
    
    # Task management commands
    subparsers.add_parser("create_task", help="Create a new task")
    
    get_task_parser = subparsers.add_parser("get_task", help="Get task status and messages")
    get_task_parser.add_argument("--task_id", required=True, help="Task ID")
    
    message_parser = subparsers.add_parser("send_message", help="Send a message to a task")
    message_parser.add_argument("--task_id", required=True, help="Task ID")
    message_parser.add_argument("--message", required=True, help="Message to send")
    
    upload_parser = subparsers.add_parser("upload_file", help="Upload a file to a task")
    upload_parser.add_argument("--task_id", required=True, help="Task ID")
    upload_parser.add_argument("--file", required=True, help="Path to file")
    upload_parser.add_argument("--description", default="", help="File description")
    
    form_parser = subparsers.add_parser("submit_form", help="Submit a form to a task")
    form_parser.add_argument("--task_id", required=True, help="Task ID")
    form_parser.add_argument("--form_data", help="JSON string with form data")
    
    # Demo commands
    subparsers.add_parser("web_search", help="Demo web search capability")
    subparsers.add_parser("image_generation", help="Demo image generation capability")
    
    image_parser = subparsers.add_parser("image_analysis", help="Demo image analysis capability")
    image_parser.add_argument("--image", required=True, help="Path to image file")
    
    receipt_parser = subparsers.add_parser("receipt_processing", help="Demo receipt processing capability")
    receipt_parser.add_argument("--receipt", required=True, help="Path to receipt image")
    
    subparsers.add_parser("currency_conversion", help="Demo currency conversion capability")
    subparsers.add_parser("data_visualization", help="Demo data visualization capability")
    subparsers.add_parser("form_submission", help="Demo form submission capability")
    
    all_parser = subparsers.add_parser("demo_all", help="Run all demos")
    all_parser.add_argument("--image", help="Path to image file for image analysis demo")
    all_parser.add_argument("--receipt", help="Path to receipt image for receipt processing demo")
    
    return parser.parse_args()

async def main():
    """Main entry point for the client."""
    args = parse_args()
    
    if not args.command:
        print("Error: Please specify a command")
        return
    
    try:
        if args.command == "agent_card":
            card = await fetch_agent_card()
            print(json.dumps(card, indent=2))
        
        elif args.command == "create_task":
            task_id = await create_task()
            print(f"Task created: {task_id}")
        
        elif args.command == "get_task":
            task = await get_task(args.task_id)
            print(json.dumps(task.dict(), indent=2))
        
        elif args.command == "send_message":
            response = await send_message(args.task_id, args.message)
            print(json.dumps(response.dict(), indent=2))
        
        elif args.command == "upload_file":
            result = await upload_file(args.task_id, args.file, args.description)
            print(json.dumps(result.dict(), indent=2))
        
        elif args.command == "submit_form":
            form_data = json.loads(args.form_data) if args.form_data else {
                "expense_type": "Travel",
                "amount": 123.45,
                "date": "2023-10-15",
                "description": "Business trip to client office",
                "currency": "USD"
            }
            response = await submit_form(args.task_id, form_data)
            print(json.dumps(response.dict(), indent=2))
        
        # Demo commands
        elif args.command == "web_search":
            await demo_web_search()
        
        elif args.command == "image_generation":
            await demo_image_generation()
        
        elif args.command == "image_analysis":
            await demo_image_analysis(args.image)
        
        elif args.command == "receipt_processing":
            await demo_receipt_processing(args.receipt)
        
        elif args.command == "currency_conversion":
            await demo_currency_conversion()
        
        elif args.command == "data_visualization":
            await demo_data_visualization()
        
        elif args.command == "form_submission":
            await demo_form_submission()
        
        elif args.command == "demo_all":
            await demo_all(args.image, args.receipt)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 