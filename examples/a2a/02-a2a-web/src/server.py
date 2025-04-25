#!/usr/bin/env python
"""
Web Integration Agent Server

An advanced A2A agent that demonstrates web capabilities including 
search, image generation, and data processing.
"""

import os
import json
import uuid
import base64
import asyncio
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Body, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

# Models for request/response schema
class TaskRequest(BaseModel):
    id: str = Field(..., description="Unique task identifier")
    sessionId: Optional[str] = Field(None, description="Optional session identifier")

class MessagePart(BaseModel):
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    mimeType: Optional[str] = None
    fileName: Optional[str] = None

class Message(BaseModel):
    role: str
    parts: List[MessagePart]

class ArtifactPart(BaseModel):
    type: str
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    mimeType: Optional[str] = None
    fileName: Optional[str] = None
    data_b64: Optional[str] = None

class Artifact(BaseModel):
    name: str
    description: str
    parts: List[ArtifactPart]

class TaskState(BaseModel):
    id: str
    sessionId: Optional[str] = None
    status: str = "active"
    messages: List[Message] = []
    artifacts: List[Artifact] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# Store tasks in memory for this example
tasks: Dict[str, TaskState] = {}

# Create FastAPI app
app = FastAPI(
    title="Web Integration Agent",
    description="An advanced A2A agent that demonstrates web capabilities",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the agent card
@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Return the agent card from the .well-known directory."""
    well_known_dir = Path(__file__).parent.parent / ".well-known"
    agent_card_path = well_known_dir / "agent.json"
    
    if not agent_card_path.exists():
        raise HTTPException(status_code=404, detail="Agent card not found")
    
    with open(agent_card_path, "r") as f:
        agent_card = json.load(f)
    
    return agent_card

# Create a new task
@app.post("/tasks")
async def create_task(task_request: TaskRequest):
    """Create a new task."""
    task_id = task_request.id
    
    if task_id in tasks:
        raise HTTPException(status_code=409, detail=f"Task with ID {task_id} already exists")
    
    task = TaskState(
        id=task_id,
        sessionId=task_request.sessionId,
        status="active",
        messages=[],
        artifacts=[],
    )
    
    tasks[task_id] = task
    return task

# Get task status
@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get the status of a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    return tasks[task_id]

# Send a message to a task
@app.post("/tasks/{task_id}/send")
async def send_message(task_id: str, message: Message):
    """Send a message to a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = tasks[task_id]
    task.messages.append(message)
    task.updated_at = datetime.now().isoformat()
    
    # Process the message
    await process_message(task_id, message)
    
    return {"status": "message received"}

# Upload a file to a task
@app.post("/tasks/{task_id}/upload")
async def upload_file(
    task_id: str,
    file: UploadFile = File(...),
    description: str = Form(None),
):
    """Upload a file to a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = tasks[task_id]
    
    # Read file content
    content = await file.read()
    base64_content = base64.b64encode(content).decode("utf-8")
    
    # Create a message with the file
    message = Message(
        role="user",
        parts=[
            MessagePart(
                type="text",
                text=description if description else f"Uploaded file: {file.filename}"
            ),
            MessagePart(
                type="file",
                mimeType=file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream",
                fileName=file.filename,
                data=base64_content
            )
        ]
    )
    
    task.messages.append(message)
    task.updated_at = datetime.now().isoformat()
    
    # Process the message
    await process_message(task_id, message)
    
    return {"status": "file uploaded"}

# Submit a form to a task
@app.post("/tasks/{task_id}/form")
async def submit_form(task_id: str, form_data: Dict[str, Any] = Body(...)):
    """Submit a form to a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    task = tasks[task_id]
    
    # Create a message with the form data
    message = Message(
        role="user",
        parts=[
            MessagePart(
                type="text",
                text="Form submission"
            ),
            MessagePart(
                type="data",
                data=form_data
            )
        ]
    )
    
    task.messages.append(message)
    task.updated_at = datetime.now().isoformat()
    
    # Process the message
    await process_message(task_id, message)
    
    return {"status": "form submitted"}

# Helper functions for message processing
async def process_message(task_id: str, message: Message):
    """Process a message from the user and generate a response."""
    task = tasks[task_id]
    
    # Extract text from message parts
    text_parts = [part.text for part in message.parts if part.type == "text" and part.text]
    text_content = " ".join(text_parts) if text_parts else ""
    
    # Extract file parts
    file_parts = [part for part in message.parts if part.type == "file"]
    
    # Extract data parts
    data_parts = [part for part in message.parts if part.type == "data"]
    
    # Simple keyword detection for demo purposes
    response_parts = []
    artifacts = []
    
    # Prepare assistant response
    if "search" in text_content.lower():
        # Web search simulation
        response_parts.append(
            MessagePart(
                type="text",
                text="I've searched the web for your query. Here are the top results:"
            )
        )
        
        search_results = await simulate_web_search(text_content)
        response_parts.append(
            MessagePart(
                type="data",
                data={"results": search_results}
            )
        )
        
        # Create a search results artifact
        artifacts.append(
            Artifact(
                name="Search Results",
                description=f"Web search results for: {text_content}",
                parts=[
                    ArtifactPart(
                        type="text",
                        text=json.dumps(search_results, indent=2)
                    )
                ]
            )
        )
    
    elif "image" in text_content.lower() and "generate" in text_content.lower():
        # Image generation simulation
        response_parts.append(
            MessagePart(
                type="text",
                text="I've generated an image based on your description:"
            )
        )
        
        # Generate placeholder image
        image_data = await simulate_image_generation(text_content)
        
        response_parts.append(
            MessagePart(
                type="file",
                mimeType="image/png",
                fileName="generated_image.png",
                data_b64=image_data
            )
        )
        
        # Create an image artifact
        artifacts.append(
            Artifact(
                name="Generated Image",
                description=f"Image generated from: {text_content}",
                parts=[
                    ArtifactPart(
                        type="file",
                        mimeType="image/png",
                        fileName="generated_image.png",
                        data_b64=image_data
                    )
                ]
            )
        )
    
    elif "analyze" in text_content.lower() and file_parts:
        # Image analysis simulation
        file_part = file_parts[0]
        
        response_parts.append(
            MessagePart(
                type="text",
                text=f"I've analyzed the image '{file_part.fileName}'. Here's what I found:"
            )
        )
        
        analysis_results = await simulate_image_analysis(file_part)
        response_parts.append(
            MessagePart(
                type="data",
                data={"analysis": analysis_results}
            )
        )
        
        # Create an analysis artifact
        artifacts.append(
            Artifact(
                name="Image Analysis",
                description=f"Analysis of image: {file_part.fileName}",
                parts=[
                    ArtifactPart(
                        type="text",
                        text=json.dumps(analysis_results, indent=2)
                    )
                ]
            )
        )
    
    elif "receipt" in text_content.lower() and file_parts:
        # Receipt processing simulation
        file_part = file_parts[0]
        
        response_parts.append(
            MessagePart(
                type="text",
                text=f"I've processed the receipt '{file_part.fileName}'. Here are the details:"
            )
        )
        
        receipt_data = await simulate_receipt_processing(file_part)
        response_parts.append(
            MessagePart(
                type="data",
                data={"receipt": receipt_data}
            )
        )
        
        # Create a structured data artifact
        artifacts.append(
            Artifact(
                name="Receipt Data",
                description=f"Extracted data from receipt: {file_part.fileName}",
                parts=[
                    ArtifactPart(
                        type="data",
                        data=receipt_data
                    ),
                    ArtifactPart(
                        type="text",
                        text=f"Vendor: {receipt_data['vendor']}\nDate: {receipt_data['date']}\nTotal: {receipt_data['total']}\nItems: {len(receipt_data['items'])}"
                    )
                ]
            )
        )
    
    elif "convert" in text_content.lower() and "currency" in text_content.lower():
        # Currency conversion simulation
        response_parts.append(
            MessagePart(
                type="text",
                text="I've converted the currency for you:"
            )
        )
        
        conversion_result = await simulate_currency_conversion(text_content)
        response_parts.append(
            MessagePart(
                type="data",
                data={"conversion": conversion_result}
            )
        )
        
        # Create a conversion artifact
        artifacts.append(
            Artifact(
                name="Currency Conversion",
                description=f"Currency conversion result",
                parts=[
                    ArtifactPart(
                        type="data",
                        data=conversion_result
                    )
                ]
            )
        )
    
    elif "chart" in text_content.lower() or "graph" in text_content.lower() or "visualize" in text_content.lower():
        # Data visualization simulation
        data_to_visualize = {}
        
        if data_parts:
            data_to_visualize = data_parts[0].data or {}
        else:
            data_to_visualize = await simulate_sample_data()
            
        response_parts.append(
            MessagePart(
                type="text",
                text="I've created a chart visualization of your data:"
            )
        )
        
        chart_image = await simulate_data_visualization(data_to_visualize)
        
        response_parts.append(
            MessagePart(
                type="file",
                mimeType="image/png",
                fileName="data_visualization.png",
                data_b64=chart_image
            )
        )
        
        # Create a visualization artifact
        artifacts.append(
            Artifact(
                name="Data Visualization",
                description="Chart generated from data",
                parts=[
                    ArtifactPart(
                        type="file",
                        mimeType="image/png",
                        fileName="data_visualization.png",
                        data_b64=chart_image
                    ),
                    ArtifactPart(
                        type="data",
                        data=data_to_visualize
                    )
                ]
            )
        )
        
    else:
        # Default response
        response_parts.append(
            MessagePart(
                type="text",
                text=f"I'm a web integration agent that can help with various tasks. I noticed you said: '{text_content}'. Here are some things I can do:\n\n"
                     f"- Web search (try 'search for...')\n"
                     f"- Generate images (try 'generate an image of...')\n"
                     f"- Analyze images (upload an image and say 'analyze this image')\n"
                     f"- Process receipts (upload a receipt image)\n"
                     f"- Convert currencies (try 'convert 100 USD to EUR')\n"
                     f"- Create data visualizations (try 'create a chart of...')"
            )
        )
    
    # Add the assistant's response to the task messages
    assistant_message = Message(
        role="assistant",
        parts=response_parts
    )
    
    task.messages.append(assistant_message)
    
    # Add any artifacts to the task
    for artifact in artifacts:
        task.artifacts.append(artifact)
    
    # Update the task status
    task.updated_at = datetime.now().isoformat()
    tasks[task_id] = task

# Simulation of web capabilities

async def simulate_web_search(query: str) -> List[Dict[str, str]]:
    """Simulate a web search with mock results."""
    await asyncio.sleep(1)  # Simulate network delay
    
    return [
        {
            "title": f"Result 1 for '{query}'",
            "url": "https://example.com/result1",
            "snippet": f"This is the first result for {query} with some interesting information..."
        },
        {
            "title": f"Result 2 for '{query}'",
            "url": "https://example.com/result2",
            "snippet": f"Here's another relevant result about {query} that might be useful..."
        },
        {
            "title": f"Result 3 for '{query}'",
            "url": "https://example.com/result3",
            "snippet": f"More information about {query} and related topics can be found here..."
        }
    ]

async def simulate_image_generation(prompt: str) -> str:
    """Simulate image generation with a placeholder image."""
    await asyncio.sleep(2)  # Simulate processing time
    
    # For demo purposes, we're creating a simple colored square
    # In a real implementation, this would call an image generation API
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create a colored image with the prompt text
    img = Image.new('RGB', (500, 300), color=(73, 109, 137))
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()
    
    # Add text to the image
    draw.text((10, 10), f"Generated image for:\n{prompt}", fill=(255, 255, 255), font=font)
    
    # Save to a bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    
    # Return base64 encoded image
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

async def simulate_image_analysis(file_part: MessagePart) -> Dict[str, Any]:
    """Simulate image analysis with mock results."""
    await asyncio.sleep(1.5)  # Simulate processing time
    
    # In a real implementation, this would extract and decode the image
    # then send it to an image analysis API
    
    return {
        "objects": ["person", "car", "tree"],
        "colors": ["blue", "red", "green"],
        "tags": ["outdoor", "daytime", "urban"],
        "confidence": 0.87,
        "dimensions": {
            "width": 800,
            "height": 600
        }
    }

async def simulate_receipt_processing(file_part: MessagePart) -> Dict[str, Any]:
    """Simulate receipt processing with mock results."""
    await asyncio.sleep(2)  # Simulate processing time
    
    return {
        "vendor": "ACME Store",
        "date": "2023-05-15",
        "time": "14:30",
        "total": "$127.84",
        "subtotal": "$115.95",
        "tax": "$11.89",
        "payment_method": "Credit Card",
        "card_last4": "1234",
        "items": [
            {"name": "Product 1", "quantity": 2, "unit_price": "$24.99", "total": "$49.98"},
            {"name": "Product 2", "quantity": 1, "unit_price": "$35.99", "total": "$35.99"},
            {"name": "Product 3", "quantity": 3, "unit_price": "$9.99", "total": "$29.97"}
        ]
    }

async def simulate_currency_conversion(text: str) -> Dict[str, Any]:
    """Simulate currency conversion with mock results."""
    await asyncio.sleep(0.5)  # Simulate processing time
    
    # Simple regex to extract currencies and amount
    import re
    
    pattern = r"convert\s+(\d+(?:\.\d+)?)\s+([A-Z]{3})\s+to\s+([A-Z]{3})"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        amount = float(match.group(1))
        from_currency = match.group(2)
        to_currency = match.group(3)
        
        # Mock conversion rates
        rates = {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 149.56,
            "CAD": 1.37,
            "AUD": 1.53,
            "CNY": 7.25
        }
        
        if from_currency in rates and to_currency in rates:
            converted_amount = amount * (rates[to_currency] / rates[from_currency])
            
            return {
                "from": {
                    "currency": from_currency,
                    "amount": amount
                },
                "to": {
                    "currency": to_currency,
                    "amount": round(converted_amount, 2)
                },
                "rate": round(rates[to_currency] / rates[from_currency], 4),
                "timestamp": datetime.now().isoformat()
            }
    
    # Default fallback
    return {
        "from": {"currency": "USD", "amount": 100},
        "to": {"currency": "EUR", "amount": 92},
        "rate": 0.92,
        "timestamp": datetime.now().isoformat()
    }

async def simulate_sample_data() -> Dict[str, Any]:
    """Generate sample data for visualization."""
    return {
        "title": "Monthly Sales Data",
        "data": [
            {"month": "Jan", "value": 65},
            {"month": "Feb", "value": 59},
            {"month": "Mar", "value": 80},
            {"month": "Apr", "value": 81},
            {"month": "May", "value": 56},
            {"month": "Jun", "value": 55},
            {"month": "Jul", "value": 40}
        ]
    }

async def simulate_data_visualization(data: Dict[str, Any]) -> str:
    """Simulate creating a chart visualization with mock image."""
    await asyncio.sleep(1.5)  # Simulate processing time
    
    # For demo purposes, creating a simple placeholder image
    # In a real implementation, this would use a plotting library
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create a white image
    img = Image.new('RGB', (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 12)
        title_font = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Draw title
    title = data.get("title", "Data Visualization")
    draw.text((20, 20), title, fill=(0, 0, 0), font=title_font)
    
    # Draw axes
    draw.line((50, 350, 550, 350), fill=(0, 0, 0), width=2)  # X-axis
    draw.line((50, 50, 50, 350), fill=(0, 0, 0), width=2)    # Y-axis
    
    # Draw data points
    if "data" in data and isinstance(data["data"], list):
        items = data["data"]
        max_value = max([item.get("value", 0) for item in items])
        bar_width = min(80, 500 // (len(items) + 1))
        
        for i, item in enumerate(items):
            value = item.get("value", 0)
            label = item.get("month", str(i))
            
            # Calculate bar height and position
            height = (value / max_value) * 280 if max_value > 0 else 0
            x = 50 + (i + 1) * (500 // (len(items) + 1))
            
            # Draw bar
            draw.rectangle(
                [x - bar_width//2, 350 - height, x + bar_width//2, 350],
                fill=(65, 105, 225)
            )
            
            # Draw label
            draw.text((x - 10, 355), label, fill=(0, 0, 0), font=font)
            
            # Draw value
            draw.text((x - 10, 350 - height - 15), str(value), fill=(0, 0, 0), font=font)
    
    # Save to a bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    
    # Return base64 encoded image
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# Main entry point
if __name__ == "__main__":
    # Ensure the required directories exist
    well_known_dir = Path(__file__).parent.parent / ".well-known"
    well_known_dir.mkdir(exist_ok=True)
    
    # Start the server
    uvicorn.run("server:app", host="0.0.0.0", port=8002, reload=True) 