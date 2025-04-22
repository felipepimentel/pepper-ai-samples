#!/usr/bin/env python3
"""Event-Driven Architecture Assistant MCP Server."""

from typing import Dict, List, Optional

from fastapi import FastAPI
from pepperpymcp import PepperFastMCP
from pydantic import BaseModel


class EventDefinition(BaseModel):
    """Event definition model."""

    name: str
    version: str
    schema: Dict
    producers: List[str]
    consumers: List[str]


class EventFlow(BaseModel):
    """Event flow model."""

    source: str
    target: str
    event_type: str
    frequency: str
    latency: Optional[float]


# Initialize MCP server
mcp = PepperFastMCP(
    "Event-Driven Architecture Assistant",
    description="Assists with event-driven architecture design and analysis",
)


@mcp.tool()
async def analyze_event_flows(flows: List[EventFlow]) -> Dict:
    """Analyze event flows for patterns and potential issues."""
    try:
        analysis = {"patterns": [], "bottlenecks": [], "suggestions": []}

        # Build flow graph
        graph = {}
        for flow in flows:
            if flow.source not in graph:
                graph[flow.source] = []
            graph[flow.source].append(
                {
                    "target": flow.target,
                    "event": flow.event_type,
                    "frequency": flow.frequency,
                    "latency": flow.latency,
                }
            )

        # Analyze patterns
        for source, targets in graph.items():
            # Check for fan-out pattern
            if len(targets) > 3:
                analysis["patterns"].append(
                    {"type": "fan-out", "source": source, "targets": len(targets)}
                )

            # Check for high latency
            high_latency_flows = [
                t
                for t in targets
                if t["latency"] and t["latency"] > 1.0  # More than 1 second
            ]
            if high_latency_flows:
                analysis["bottlenecks"].extend(
                    [
                        {
                            "source": source,
                            "target": flow["target"],
                            "latency": flow["latency"],
                        }
                        for flow in high_latency_flows
                    ]
                )

        # Generate suggestions
        if analysis["bottlenecks"]:
            analysis["suggestions"].append(
                "Consider implementing event buffering or batch processing for high-latency flows"
            )

        for pattern in analysis["patterns"]:
            if pattern["type"] == "fan-out" and pattern["targets"] > 5:
                analysis["suggestions"].append(
                    f"Consider using a message broker for {pattern['source']} fan-out pattern"
                )

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def validate_event_schema(event: EventDefinition) -> Dict:
    """Validate event schema and suggest improvements."""
    try:
        validation = {"issues": [], "suggestions": []}

        # Check schema version
        if not event.version:
            validation["issues"].append("Missing event version")
            validation["suggestions"].append(
                "Add semantic versioning to track schema evolution"
            )

        # Check schema fields
        schema = event.schema
        if "timestamp" not in schema:
            validation["suggestions"].append("Add timestamp field for event ordering")

        if "id" not in schema:
            validation["suggestions"].append(
                "Add unique identifier field for event tracking"
            )

        # Check for schema best practices
        if not any(field.endswith("At") for field in schema.keys()):
            validation["suggestions"].append(
                "Consider adding temporal fields with 'At' suffix (e.g., createdAt, updatedAt)"
            )

        return {"success": True, "validation": validation}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_event_handlers(event: EventDefinition) -> Dict:
    """Generate event handler templates for different messaging systems."""
    try:
        templates = {}

        # NATS handler
        nats_handler = f"""
async def handle_{event.name.lower()}_nats(msg):
    try:
        data = json.loads(msg.data.decode())
        # Validate against schema
        validate_{event.name.lower()}_event(data)
        # Process event
        await process_{event.name.lower()}_event(data)
        await msg.ack()
    except Exception as e:
        # Error handling
        await msg.nak()
        
# Subscribe to event
await nc.subscribe(
    f"{event.name.lower()}.>",
    cb=handle_{event.name.lower()}_nats
)
"""
        templates["nats"] = nats_handler

        # Kafka handler
        kafka_handler = f"""
def handle_{event.name.lower()}_kafka(consumer):
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Error: {{msg.error()}}")
                    break
            
            data = json.loads(msg.value().decode('utf-8'))
            # Validate against schema
            validate_{event.name.lower()}_event(data)
            # Process event
            process_{event.name.lower()}_event(data)
            consumer.commit(msg)
    except Exception as e:
        print(f"Error: {{e}}")
"""
        templates["kafka"] = kafka_handler

        # RabbitMQ handler
        rabbitmq_handler = f"""
async def handle_{event.name.lower()}_rabbitmq(message):
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            # Validate against schema
            validate_{event.name.lower()}_event(data)
            # Process event
            await process_{event.name.lower()}_event(data)
        except Exception as e:
            # Error handling
            await message.reject(requeue=False)
            
# Bind queue
channel = await connection.channel()
queue = await channel.declare_queue(
    f"{event.name.lower()}_queue",
    durable=True
)
await queue.consume(handle_{event.name.lower()}_rabbitmq)
"""
        templates["rabbitmq"] = rabbitmq_handler

        return {"success": True, "templates": templates}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def suggest_event_patterns(flows: List[EventFlow]) -> Dict:
    """Suggest event patterns based on flow analysis."""
    try:
        suggestions = []

        # Analyze flow patterns
        source_counts = {}
        target_counts = {}

        for flow in flows:
            source_counts[flow.source] = source_counts.get(flow.source, 0) + 1
            target_counts[flow.target] = target_counts.get(flow.target, 0) + 1

        # Suggest patterns based on topology
        for source, count in source_counts.items():
            if count > 3:
                suggestions.append(
                    {
                        "pattern": "Publish-Subscribe",
                        "service": source,
                        "reason": f"Service emits events to {count} consumers",
                        "implementation": "Consider using a topic-based message broker",
                    }
                )

        for target, count in target_counts.items():
            if count > 3:
                suggestions.append(
                    {
                        "pattern": "Event Aggregation",
                        "service": target,
                        "reason": f"Service consumes events from {count} producers",
                        "implementation": "Consider implementing event aggregation pattern",
                    }
                )

        # Check for chain patterns
        chain = []
        visited = set()

        def build_chain(service):
            chain.append(service)
            visited.add(service)

            next_services = [
                flow.target
                for flow in flows
                if flow.source == service and flow.target not in visited
            ]

            for next_service in next_services:
                build_chain(next_service)

            if len(chain) > 3:
                suggestions.append(
                    {
                        "pattern": "Saga",
                        "services": chain.copy(),
                        "reason": "Long chain of event dependencies detected",
                        "implementation": "Consider implementing Saga pattern for distributed transactions",
                    }
                )

            chain.pop()

        for flow in flows:
            if flow.source not in visited:
                build_chain(flow.source)

        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Add FastAPI integration
app = FastAPI(title="Event-Driven Architecture Assistant")
mcp.add_web_client()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8010, reload=True)
