#!/usr/bin/env python
"""
Weather Insights A2A-MCP Integration Example

This example demonstrates the integration between:
1. A2A (Agent-to-Agent) protocol for weather insights capabilities
2. MCP (Model Context Protocol) for weather data retrieval and analysis tools

The application provides:
- Weather data retrieval using MCP tools
- Weather analysis and insights using A2A capabilities
- Integration between A2A and MCP using a bridge
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import required libraries
import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

# Import A2A and MCP libraries
from libs.pepperpya2a import create_a2a_server
from libs.pepperpymcp import create_mcp_server

# Import the A2A-MCP bridge
from a2a_mcp_bridge import create_a2a_mcp_bridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variables
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Initialize FastAPI for the web interface
app = FastAPI(title="Weather Insights")

# Set up templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Initialize MCP server
mcp_server = create_mcp_server(
    name="Weather Data MCP",
    description="MCP server providing weather data tools"
)

# Initialize A2A server
a2a_server = create_a2a_server(
    agent_id="weather-insights",
    name="Weather Insights Agent",
    description="A2A agent providing weather insights capabilities"
)

# A2A server will share the same FastAPI app
a2a_server.app = app

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for request/response
class LocationRequest(BaseModel):
    """Location request model."""
    location: str
    days: int = 5

class WeatherResponse(BaseModel):
    """Weather data response model."""
    location: str
    current: Dict[str, Any]
    forecast: Optional[List[Dict[str, Any]]] = None

class WeatherInsightResponse(BaseModel):
    """Weather insight response model."""
    location: str
    insights: str
    trends: str
    recommendations: str
    data: Dict[str, Any]

# MCP Tool: Get current weather
@mcp_server.tool()
async def get_current_weather(location: str) -> Dict[str, Any]:
    """
    Get current weather data for a location.
    
    Args:
        location: City name or location
        
    Returns:
        Dictionary with current weather data
    """
    logger.info(f"Getting current weather for {location}")
    
    if not WEATHER_API_KEY:
        # Use simulated data if no API key is provided
        return _get_simulated_weather(location)
    
    try:
        # Make API call to OpenWeatherMap
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Format the response
                    return {
                        "location": f"{data['name']}, {data['sys']['country']}",
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "condition": data["weather"][0]["description"],
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "wind_speed": data["wind"]["speed"],
                        "wind_direction": data["wind"]["deg"],
                        "visibility": data.get("visibility", 0) / 1000,  # Convert to km
                        "timestamp": datetime.utcfromtimestamp(data["dt"]).isoformat()
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"API error: {error_text}")
                    return _get_simulated_weather(location)
    except Exception as e:
        logger.error(f"Error getting weather: {str(e)}")
        return _get_simulated_weather(location)

# MCP Tool: Get weather forecast
@mcp_server.tool()
async def get_weather_forecast(location: str, days: int = 5) -> Dict[str, Any]:
    """
    Get weather forecast for a location.
    
    Args:
        location: City name or location
        days: Number of days to forecast (max 5)
        
    Returns:
        Dictionary with forecast data
    """
    logger.info(f"Getting {days}-day forecast for {location}")
    
    if not WEATHER_API_KEY:
        # Use simulated data if no API key is provided
        return _get_simulated_forecast(location, days)
    
    try:
        # Make API call to OpenWeatherMap
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": "metric",
            "cnt": min(days * 8, 40)  # Maximum 5 days (40 3-hour intervals)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Process and format the forecast data
                    processed_data = _process_forecast_data(data, days)
                    return processed_data
                else:
                    error_text = await response.text()
                    logger.error(f"API error: {error_text}")
                    return _get_simulated_forecast(location, days)
    except Exception as e:
        logger.error(f"Error getting forecast: {str(e)}")
        return _get_simulated_forecast(location, days)

# A2A Capability: Analyze weather trends
@a2a_server.capability("analyzeWeatherTrends")
async def analyze_weather_trends(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze weather trends based on forecast data.
    
    Args:
        data: Dictionary containing location and optional days parameter
        
    Returns:
        Analysis of weather trends
    """
    logger.info("Analyzing weather trends")
    input_data = data.get("input", {})
    location = input_data.get("location", "Unknown")
    days = input_data.get("days", 5)
    
    try:
        # Get the forecast data using MCP tool
        # This is a direct call to get_weather_forecast which is a registered MCP tool
        forecast_data = await get_weather_forecast(location, days)
        
        # Simple trend analysis logic (in a real app, this would be more sophisticated)
        trends = _analyze_trends(forecast_data)
        
        return {
            "location": forecast_data.get("location", location),
            "trends": trends,
            "data": forecast_data
        }
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return {
            "location": location,
            "trends": "Unable to analyze trends due to an error.",
            "error": str(e)
        }

# A2A Capability: Generate weather report
@a2a_server.capability("generateWeatherReport")
async def generate_weather_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a comprehensive weather report.
    
    Args:
        data: Dictionary containing location and optional days parameter
        
    Returns:
        Comprehensive weather report with current conditions, forecast, and insights
    """
    logger.info("Generating weather report")
    input_data = data.get("input", {})
    location = input_data.get("location", "Unknown")
    days = input_data.get("days", 5)
    
    try:
        # Get current weather using MCP tool
        current_weather = await get_current_weather(location)
        
        # Get forecast using MCP tool
        forecast_data = await get_weather_forecast(location, days)
        
        # Analyze trends using another A2A capability
        trends_data = await analyze_weather_trends(data)
        
        # Generate insights and recommendations
        insights = _generate_insights(current_weather, forecast_data)
        recommendations = _generate_recommendations(current_weather, forecast_data)
        
        # Create a report using the template
        report_data = {
            "location": current_weather.get("location", location),
            "current": current_weather,
            "forecast": forecast_data.get("forecast", []),
            "forecast_days": days,
            "insights": insights,
            "trends": trends_data.get("trends", "No trend data available."),
            "recommendations": recommendations
        }
        
        # Load and render template
        template_path = Path(__file__).parent / "templates" / "weather_report.template"
        with open(template_path, "r") as f:
            template_content = f.read()
        
        # Simple template rendering (in a real app, use proper template engine)
        report = _render_template(template_content, report_data)
        
        return {
            "location": current_weather.get("location", location),
            "report": report,
            "data": {
                "current": current_weather,
                "forecast": forecast_data,
                "insights": insights,
                "trends": trends_data.get("trends", ""),
                "recommendations": recommendations
            }
        }
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return {
            "location": location,
            "report": f"Unable to generate report due to an error: {str(e)}",
            "error": str(e)
        }

# Create the bridge between A2A and MCP
bridge = create_a2a_mcp_bridge(a2a_server, mcp_server, "weather-bridge")

# Web UI routes
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    """Render the main web UI."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/weather/{location}")
async def get_weather(location: str):
    """API endpoint to get current weather."""
    weather_data = await get_current_weather(location)
    return weather_data

@app.get("/api/forecast/{location}")
async def get_forecast(location: str, days: int = 5):
    """API endpoint to get weather forecast."""
    forecast_data = await get_weather_forecast(location, days)
    return forecast_data

@app.get("/api/insights/{location}")
async def get_insights(location: str, days: int = 5):
    """API endpoint to get weather insights."""
    # Call the A2A capability through the bridge
    data = {
        "input": {
            "location": location,
            "days": days
        }
    }
    insights_data = await a2a_server.capabilities["analyzeWeatherTrends"]["handler"](data)
    return insights_data

@app.get("/api/report/{location}")
async def get_report(location: str, days: int = 5):
    """API endpoint to get a comprehensive weather report."""
    # Call the A2A capability through the bridge
    data = {
        "input": {
            "location": location,
            "days": days
        }
    }
    report_data = await a2a_server.capabilities["generateWeatherReport"]["handler"](data)
    return report_data

# Helper functions
def _get_simulated_weather(location: str) -> Dict[str, Any]:
    """Generate simulated weather data for demo purposes."""
    locations = {
        "New York": {"temp": 22, "condition": "Clear sky", "humidity": 65, "wind": 3.5},
        "London": {"temp": 15, "condition": "Light rain", "humidity": 80, "wind": 5.1},
        "Tokyo": {"temp": 28, "condition": "Scattered clouds", "humidity": 70, "wind": 2.8},
        "Sydney": {"temp": 25, "condition": "Sunny", "humidity": 60, "wind": 4.2},
        "Paris": {"temp": 18, "condition": "Partly cloudy", "humidity": 72, "wind": 3.9}
    }
    
    # Default weather if location not found
    weather = locations.get(location, {"temp": 20, "condition": "Clear", "humidity": 65, "wind": 3.0})
    
    # Expand with additional data
    return {
        "location": f"{location}, Simulated",
        "temperature": weather["temp"],
        "feels_like": weather["temp"] - 2,
        "condition": weather["condition"],
        "humidity": weather["humidity"],
        "pressure": 1013,
        "wind_speed": weather["wind"],
        "wind_direction": 180,
        "visibility": 10,
        "timestamp": datetime.now().isoformat()
    }

def _get_simulated_forecast(location: str, days: int = 5) -> Dict[str, Any]:
    """Generate simulated forecast data for demo purposes."""
    # Get simulated current weather as starting point
    current = _get_simulated_weather(location)
    forecast = []
    
    for i in range(days):
        # Create simulated day with variations
        day_date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        temp_variation = (i % 3) - 1  # -1, 0, or 1 variation
        
        forecast.append({
            "date": day_date,
            "temp_max": current["temperature"] + temp_variation + 2,
            "temp_min": current["temperature"] + temp_variation - 2,
            "condition": current["condition"],
            "precipitation": (i * 10) % 30,  # 0, 10, 20% precipitation
            "wind_speed": current["wind_speed"] + (i % 3 - 1)
        })
    
    return {
        "location": current["location"],
        "forecast": forecast
    }

def _process_forecast_data(data: Dict[str, Any], days: int) -> Dict[str, Any]:
    """Process and format OpenWeatherMap forecast data."""
    # Extract location info
    location = f"{data['city']['name']}, {data['city']['country']}"
    
    # Group forecast by day (since API returns 3-hour intervals)
    daily_forecasts = {}
    for item in data["list"]:
        timestamp = datetime.utcfromtimestamp(item["dt"])
        day = timestamp.strftime("%Y-%m-%d")
        
        if day not in daily_forecasts:
            daily_forecasts[day] = []
        
        daily_forecasts[day].append({
            "time": timestamp.strftime("%H:%M"),
            "temp": item["main"]["temp"],
            "feels_like": item["main"]["feels_like"],
            "condition": item["weather"][0]["description"],
            "humidity": item["main"]["humidity"],
            "pressure": item["main"]["pressure"],
            "wind_speed": item["wind"]["speed"],
            "precipitation": item.get("pop", 0) * 100  # Probability of precipitation
        })
    
    # Aggregate daily data
    forecast = []
    for day, intervals in sorted(daily_forecasts.items())[:days]:
        # Calculate daily min/max
        temps = [interval["temp"] for interval in intervals]
        conditions = [interval["condition"] for interval in intervals]
        precip = [interval["precipitation"] for interval in intervals]
        wind = [interval["wind_speed"] for interval in intervals]
        
        # Find most common condition
        condition_counts = {}
        for condition in conditions:
            if condition not in condition_counts:
                condition_counts[condition] = 0
            condition_counts[condition] += 1
        main_condition = max(condition_counts.items(), key=lambda x: x[1])[0]
        
        forecast.append({
            "date": day,
            "temp_max": max(temps),
            "temp_min": min(temps),
            "condition": main_condition,
            "precipitation": max(precip),
            "wind_speed": sum(wind) / len(wind)  # Average wind speed
        })
    
    return {
        "location": location,
        "forecast": forecast
    }

def _analyze_trends(forecast_data: Dict[str, Any]) -> str:
    """Analyze weather trends based on forecast data."""
    forecast = forecast_data.get("forecast", [])
    if not forecast:
        return "No forecast data available for trend analysis."
    
    # Analyze temperature trend
    temps = [day["temp_max"] for day in forecast]
    temp_diff = temps[-1] - temps[0]
    
    # Analyze conditions
    conditions = [day["condition"].lower() for day in forecast]
    has_rain = any("rain" in condition for condition in conditions)
    has_clear = any("clear" in condition or "sunny" in condition for condition in conditions)
    
    # Generate trend analysis
    trends = []
    
    if temp_diff > 3:
        trends.append(f"Temperatures are warming significantly over the next {len(forecast)} days.")
    elif temp_diff < -3:
        trends.append(f"Temperatures are cooling significantly over the next {len(forecast)} days.")
    elif abs(temp_diff) <= 1:
        trends.append(f"Temperatures are stable over the next {len(forecast)} days.")
    else:
        warming = "warming" if temp_diff > 0 else "cooling"
        trends.append(f"Temperatures are gradually {warming} over the next {len(forecast)} days.")
    
    # Analyze precipitation pattern
    precip_pattern = [day["precipitation"] for day in forecast]
    avg_precip = sum(precip_pattern) / len(precip_pattern)
    
    if avg_precip > 50:
        trends.append("There is a high chance of precipitation during this period.")
    elif avg_precip > 30:
        trends.append("There is a moderate chance of precipitation during this period.")
    else:
        trends.append("Precipitation chances are relatively low during this period.")
    
    # Condition changes
    if has_rain and has_clear:
        trends.append("The weather will be variable with both sunny and rainy periods.")
    elif has_rain:
        trends.append("Mostly wet conditions are expected during this period.")
    elif has_clear:
        trends.append("Mostly clear conditions are expected during this period.")
    
    return "\n".join(trends)

def _generate_insights(current: Dict[str, Any], forecast: Dict[str, Any]) -> str:
    """Generate weather insights based on current and forecast data."""
    insights = []
    
    # Current weather insights
    temp = current.get("temperature", 0)
    humidity = current.get("humidity", 0)
    wind = current.get("wind_speed", 0)
    
    if temp > 30:
        insights.append("Current temperatures are very high. Stay hydrated and seek shade when outdoors.")
    elif temp < 5:
        insights.append("Current temperatures are very low. Dress warmly when going outside.")
    
    if humidity > 80:
        insights.append("Humidity is high, which may make it feel more uncomfortable outside.")
    elif humidity < 30:
        insights.append("Humidity is low, which may cause dry skin and eyes.")
    
    if wind > 8:
        insights.append("Wind speeds are elevated, which may affect outdoor activities.")
    
    # Forecast insights
    forecast_list = forecast.get("forecast", [])
    if forecast_list:
        max_temps = [day["temp_max"] for day in forecast_list]
        min_temps = [day["temp_min"] for day in forecast_list]
        conditions = [day["condition"].lower() for day in forecast_list]
        
        temp_range = max(max_temps) - min(min_temps)
        if temp_range > 10:
            insights.append(f"There will be significant temperature variations in the coming days (range of {temp_range:.1f}°C).")
        
        if any("rain" in condition for condition in conditions):
            rain_days = sum(1 for condition in conditions if "rain" in condition)
            insights.append(f"Rain is expected on {rain_days} of the next {len(forecast_list)} days.")
    
    if not insights:
        insights.append("Weather conditions appear to be moderate with no significant concerns.")
    
    return "\n".join(insights)

def _generate_recommendations(current: Dict[str, Any], forecast: Dict[str, Any]) -> str:
    """Generate recommendations based on weather data."""
    recommendations = []
    
    # Current weather recommendations
    temp = current.get("temperature", 0)
    condition = current.get("condition", "").lower()
    
    if "rain" in condition or "shower" in condition:
        recommendations.append("Carry an umbrella or raincoat today.")
    elif "snow" in condition:
        recommendations.append("Wear warm, waterproof clothing and appropriate footwear.")
    elif temp > 28:
        recommendations.append("Stay hydrated and use sun protection when outdoors.")
    elif temp < 10:
        recommendations.append("Dress in warm layers today.")
    
    # Forecast-based recommendations
    forecast_list = forecast.get("forecast", [])
    if forecast_list:
        conditions = [day["condition"].lower() for day in forecast_list]
        
        if any("rain" in condition for condition in conditions):
            recommendations.append("Plan indoor activities for rainy days in the forecast.")
        
        if any(day["temp_max"] > 28 for day in forecast_list):
            recommendations.append("There will be some hot days ahead - plan outdoor activities for cooler parts of the day.")
        
        if any(day["temp_min"] < 5 for day in forecast_list):
            recommendations.append("Cold nights expected - ensure heating systems are working properly.")
    
    if not recommendations:
        recommendations.append("Weather conditions are favorable for most outdoor activities.")
    
    return "\n".join(recommendations)

def _render_template(template: str, data: Dict[str, Any]) -> str:
    """
    Simple template rendering function.
    
    This is a very basic implementation - in production, use a proper template engine.
    """
    result = template
    
    # Replace simple variables
    for key, value in data.items():
        if isinstance(value, (str, int, float)):
            result = result.replace("{{" + key + "}}", str(value))
    
    # Handle nested dictionaries
    for key, value in data.items():
        if isinstance(value, dict):
            for subkey, subvalue in value.items():
                result = result.replace("{{" + key + "." + subkey + "}}", str(subvalue))
    
    # Very simple loop handling (for demonstration only)
    # This only works for the specific format in our template
    for key, value in data.items():
        if isinstance(value, list) and value:
            # Find loop blocks
            start_tag = f"{{% for day in {key} %}}"
            end_tag = "{% endfor %}"
            
            if start_tag in result and end_tag in result:
                # Extract the loop template
                start_pos = result.find(start_tag)
                end_pos = result.find(end_tag, start_pos)
                
                if start_pos >= 0 and end_pos >= 0:
                    loop_template = result[start_pos + len(start_tag):end_pos]
                    loop_output = []
                    
                    # Process each item
                    for item in value:
                        item_result = loop_template
                        # Replace item variables
                        for item_key, item_value in item.items():
                            item_result = item_result.replace("{{day." + item_key + "}}", str(item_value))
                        loop_output.append(item_result)
                    
                    # Replace the entire loop block
                    result = result[:start_pos] + "".join(loop_output) + result[end_pos + len(end_tag):]
    
    return result

# Create a simple HTML index page
@app.on_event("startup")
async def startup_event():
    # Create a simple index.html file if it doesn't exist
    templates_dir = Path(__file__).parent / "templates"
    index_path = templates_dir / "index.html"
    
    if not index_path.exists():
        # Create a simple HTML interface
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weather Insights - A2A and MCP Integration</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #2c3e50; }
                .form-group { margin-bottom: 15px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input, select, button { padding: 8px; width: 100%; }
                button { background-color: #3498db; color: white; border: none; cursor: pointer; }
                button:hover { background-color: #2980b9; }
                .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; white-space: pre-wrap; }
            </style>
        </head>
        <body>
            <h1>Weather Insights - A2A and MCP Integration</h1>
            <p>This example demonstrates the integration between A2A and MCP protocols for weather data and insights.</p>
            
            <div class="form-group">
                <label for="location">Location:</label>
                <input type="text" id="location" placeholder="Enter city name" value="New York">
            </div>
            
            <div class="form-group">
                <label for="days">Forecast Days:</label>
                <select id="days">
                    <option value="1">1 day</option>
                    <option value="3">3 days</option>
                    <option value="5" selected>5 days</option>
                </select>
            </div>
            
            <div class="form-group">
                <button onclick="getCurrentWeather()">Get Current Weather</button>
            </div>
            
            <div class="form-group">
                <button onclick="getForecast()">Get Weather Forecast</button>
            </div>
            
            <div class="form-group">
                <button onclick="getInsights()">Analyze Weather Trends</button>
            </div>
            
            <div class="form-group">
                <button onclick="getReport()">Generate Complete Report</button>
            </div>
            
            <div id="result" class="result">Results will appear here...</div>
            
            <script>
                function getCurrentWeather() {
                    const location = document.getElementById('location').value;
                    fetch(`/api/weather/${encodeURIComponent(location)}`)
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('result').textContent = 
                                JSON.stringify(data, null, 2);
                        })
                        .catch(error => {
                            document.getElementById('result').textContent = 
                                `Error: ${error.message}`;
                        });
                }
                
                function getForecast() {
                    const location = document.getElementById('location').value;
                    const days = document.getElementById('days').value;
                    fetch(`/api/forecast/${encodeURIComponent(location)}?days=${days}`)
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('result').textContent = 
                                JSON.stringify(data, null, 2);
                        })
                        .catch(error => {
                            document.getElementById('result').textContent = 
                                `Error: ${error.message}`;
                        });
                }
                
                function getInsights() {
                    const location = document.getElementById('location').value;
                    const days = document.getElementById('days').value;
                    fetch(`/api/insights/${encodeURIComponent(location)}?days=${days}`)
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('result').textContent = 
                                JSON.stringify(data, null, 2);
                        })
                        .catch(error => {
                            document.getElementById('result').textContent = 
                                `Error: ${error.message}`;
                        });
                }
                
                function getReport() {
                    const location = document.getElementById('location').value;
                    const days = document.getElementById('days').value;
                    fetch(`/api/report/${encodeURIComponent(location)}?days=${days}`)
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('result').textContent = data.report || 
                                JSON.stringify(data, null, 2);
                        })
                        .catch(error => {
                            document.getElementById('result').textContent = 
                                `Error: ${error.message}`;
                        });
                }
            </script>
        </body>
        </html>
        """
        
        # Ensure directory exists
        templates_dir.mkdir(exist_ok=True)
        
        # Write the file
        with open(index_path, "w") as f:
            f.write(html_content)

# Run the servers
async def run_servers():
    """Run both A2A and MCP servers using asyncio."""
    # Start the FastAPI server (used by A2A)
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    # Create tasks
    fastapi_task = asyncio.create_task(server.serve())
    mcp_task = asyncio.create_task(mcp_server._run_async(host="0.0.0.0", port=8000))
    
    # Wait for both servers
    await asyncio.gather(fastapi_task, mcp_task)

if __name__ == "__main__":
    logger.info("Starting Weather Insights servers (A2A on port 8080, MCP on port 8000)")
    try:
        asyncio.run(run_servers())
    except KeyboardInterrupt:
        logger.info("Servers stopped by user")
    except Exception as e:
        logger.exception(f"Error running servers: {str(e)}") 