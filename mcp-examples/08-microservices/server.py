#!/usr/bin/env python3
"""Microservices Assistant MCP Server."""

from typing import Dict, List

from pepperpymcp import PepperFastMCP
from fastapi import FastAPI
from jaeger_client import Config
from kubernetes import client, config
from pydantic import BaseModel


class ServiceDefinition(BaseModel):
    """Service definition model."""

    name: str
    dependencies: List[str]
    apis: List[Dict]
    resources: Dict[str, str]


class ServiceAnalysis(BaseModel):
    """Service analysis model."""

    service_name: str
    metrics: Dict[str, float]
    dependencies: List[str]
    issues: List[str]


# Initialize MCP server
mcp = PepperFastMCP(
    "Microservices Assistant",
    description="Assists with microservices design and analysis",
)


@mcp.tool()
async def analyze_service_boundaries(services: List[ServiceDefinition]) -> Dict:
    """Analyze and suggest service boundaries based on domain-driven design."""
    try:
        analysis = {"boundaries": [], "suggestions": [], "issues": []}

        # Analyze service coupling
        for service in services:
            coupling_score = len(service.dependencies) / len(services)
            if coupling_score > 0.5:
                analysis["issues"].append(f"High coupling detected in {service.name}")
                analysis["suggestions"].append(
                    f"Consider breaking down {service.name} into smaller services"
                )

        # Check for circular dependencies
        dependency_graph = {s.name: s.dependencies for s in services}
        visited = set()
        path = []

        def has_cycle(node):
            visited.add(node)
            path.append(node)

            for neighbor in dependency_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in path:
                    analysis["issues"].append(
                        f"Circular dependency detected: {' -> '.join(path[path.index(neighbor) :])}"
                    )
                    return True

            path.pop()
            return False

        for service in services:
            if service.name not in visited:
                has_cycle(service.name)

        return analysis
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def monitor_service_health(service_name: str) -> Dict:
    """Monitor health and metrics of a microservice."""
    try:
        # Initialize Kubernetes client
        config.load_kube_config()
        v1 = client.CoreV1Api()

        # Get pod metrics
        pod_metrics = []
        pods = v1.list_namespaced_pod(
            namespace="default", label_selector=f"app={service_name}"
        )

        for pod in pods.items:
            metrics = {
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "restarts": pod.status.container_statuses[0].restart_count,
                "age": (datetime.now() - pod.metadata.creation_timestamp).days,
            }
            pod_metrics.append(metrics)

        # Initialize tracing
        tracer = Config(
            config={
                "sampler": {"type": "const", "param": 1},
                "logging": True,
            },
            service_name=service_name,
        ).initialize_tracer()

        return {
            "success": True,
            "pod_metrics": pod_metrics,
            "traces": tracer.get_spans(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def generate_service_template(service_def: ServiceDefinition) -> Dict:
    """Generate a template for a new microservice."""
    try:
        # Generate Dockerfile
        dockerfile = """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
"""

        # Generate docker-compose.yml
        docker_compose = f"""version: '3'
services:
  {service_def.name}:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=development
    depends_on:
      {["      - " + dep for dep in service_def.dependencies]}
"""

        # Generate kubernetes manifests
        k8s_deployment = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_def.name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {service_def.name}
  template:
    metadata:
      labels:
        app: {service_def.name}
    spec:
      containers:
      - name: {service_def.name}
        image: {service_def.name}:latest
        resources:
          requests:
            memory: "64Mi"
            cpu: "250m"
          limits:
            memory: "128Mi"
            cpu: "500m"
"""

        return {
            "success": True,
            "templates": {
                "Dockerfile": dockerfile,
                "docker-compose.yml": docker_compose,
                "k8s/deployment.yml": k8s_deployment,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def analyze_service_communication(services: List[ServiceDefinition]) -> Dict:
    """Analyze and optimize service communication patterns."""
    try:
        analysis = {"patterns": [], "issues": [], "suggestions": []}

        for service in services:
            # Analyze API patterns
            for api in service.apis:
                # Check for synchronous communication
                if api.get("type") == "sync":
                    analysis["patterns"].append(
                        {
                            "service": service.name,
                            "pattern": "synchronous",
                            "endpoint": api.get("endpoint"),
                        }
                    )

                    # Suggest async alternatives
                    if api.get("frequency", "low") == "high":
                        analysis["suggestions"].append(
                            {
                                "service": service.name,
                                "suggestion": f"Consider using async communication for high-frequency endpoint {api['endpoint']}",
                            }
                        )

            # Check resource usage
            for resource, amount in service.resources.items():
                try:
                    amount_float = float(amount.rstrip("Mi"))
                    if amount_float > 1000:
                        analysis["issues"].append(
                            {
                                "service": service.name,
                                "issue": f"High {resource} usage detected",
                            }
                        )
                except ValueError:
                    pass

        return {"success": True, "analysis": analysis}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Add FastAPI integration
app = FastAPI(title="Microservices Assistant")
mcp.add_web_client()

if __name__ == "__main__":
    try:
        import uvicorn
        mcp.run()
    finally:
        # Cleanup code 
        pass

