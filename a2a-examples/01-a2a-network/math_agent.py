#!/usr/bin/env python
"""
Math Agent for the A2A network.

This agent provides mathematical capabilities such as calculations, statistics, unit conversions, and finance calculations.
"""

import argparse
import asyncio
import logging
import math
import os
import re
import statistics
import sys
from typing import Any, Dict

# Add parent directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from libs.pepperpya2a.src.pepperpya2a import create_a2a_server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MathAgent:
    """Math agent that provides various mathematical capabilities."""

    def __init__(self, host: str = "localhost", port: int = 8082):
        """
        Initialize the math agent.

        Args:
            host: Host to bind the agent server
            port: Port to bind the agent server
        """
        self.host = host
        self.port = port
        self.server = create_a2a_server(
            name="Math Specialist",
            description="Provides mathematical calculations, statistics, unit conversions, and finance calculations",
            system_prompt="You are a mathematical specialist agent capable of calculations, statistics, and conversions",
            port=port,
        )

        # Register capabilities
        self.server.register_capability(
            name="calculate",
            description="Evaluate a mathematical expression",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate",
                    }
                },
                "required": ["expression"],
            },
            handler=self.calculate,
        )

        self.server.register_capability(
            name="statistics_calc",
            description="Perform statistical calculations on a list of numbers",
            input_schema={
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of numbers to analyze",
                    },
                    "operation": {
                        "type": "string",
                        "description": "Statistical operation to perform (mean, median, mode, stdev, variance, all)",
                        "enum": ["mean", "median", "mode", "stdev", "variance", "all"],
                    },
                },
                "required": ["numbers", "operation"],
            },
            handler=self.statistics_calc,
        )

        self.server.register_capability(
            name="convert_units",
            description="Convert between different units of measurement",
            input_schema={
                "type": "object",
                "properties": {
                    "value": {"type": "number", "description": "The value to convert"},
                    "from_unit": {"type": "string", "description": "The source unit"},
                    "to_unit": {"type": "string", "description": "The target unit"},
                    "unit_type": {
                        "type": "string",
                        "description": "The type of unit (length, mass, volume, temperature, time, area)",
                        "enum": [
                            "length",
                            "mass",
                            "volume",
                            "temperature",
                            "time",
                            "speed",
                            "area",
                        ],
                    },
                },
                "required": ["value", "from_unit", "to_unit"],
            },
            handler=self.convert_units,
        )

        self.server.register_capability(
            name="finance_calc",
            description="Perform financial calculations such as compound interest, loan payments, present/future value",
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The financial operation to perform",
                        "enum": [
                            "compound_interest",
                            "loan_payment",
                            "present_value",
                            "future_value",
                        ],
                    },
                    "principal": {
                        "type": "number",
                        "description": "The principal amount",
                    },
                    "rate": {
                        "type": "number",
                        "description": "The interest rate (decimal)",
                    },
                    "time": {
                        "type": "number",
                        "description": "The time period (in years)",
                    },
                    "periods": {
                        "type": "number",
                        "description": "Number of compounding periods per year",
                        "default": 1,
                    },
                },
                "required": ["operation", "principal", "rate", "time"],
            },
            handler=self.finance_calc,
        )

    def _safe_eval(self, expression: str) -> float:
        """
        Safely evaluate a mathematical expression.

        Args:
            expression: Mathematical expression as a string

        Returns:
            Result of the evaluation

        Raises:
            ValueError: If the expression is invalid or potentially dangerous
        """
        # Remove all whitespace
        expression = expression.strip()

        # Check for potentially dangerous operations
        if any(
            keyword in expression
            for keyword in ["import", "exec", "eval", "compile", "open", "__"]
        ):
            raise ValueError("Potentially dangerous expression detected")

        # Replace common mathematical functions with math equivalents
        expression = expression.replace("^", "**")

        # Extract all variable/function names used in the expression
        names = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", expression))

        # Only allow specific math functions and constants
        allowed_names = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "abs": abs,
            "pi": math.pi,
            "e": math.e,
        }

        # Check if all names in the expression are allowed
        for name in names:
            if name not in allowed_names:
                raise ValueError(f"Unknown function or variable: {name}")

        # Evaluate the expression with the allowed functions
        return eval(expression, {"__builtins__": {}}, allowed_names)

    async def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression.

        Args:
            data: Dictionary containing the expression

        Returns:
            Result of the calculation
        """
        expression = data.get("expression", "")

        if not expression:
            return {"error": "Expression is required", "status": "error"}

        logger.info(f"Calculating expression: {expression}")

        try:
            # Clean up the expression
            expression = re.sub(r"[^\d+\-*/().^a-zA-Z\s]", "", expression)

            # Evaluate the expression
            result = self._safe_eval(expression)

            return {"result": result, "expression": expression, "status": "success"}
        except Exception as e:
            logger.error(f"Error calculating expression: {str(e)}")
            return {"error": str(e), "expression": expression, "status": "error"}

    async def statistics_calc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform statistical calculations on a list of numbers.

        Args:
            data: Dictionary containing the numbers and operation

        Returns:
            Results of the statistical calculations
        """
        numbers = data.get("numbers", [])
        operation = data.get("operation", "all")

        if not numbers:
            return {"error": "Numbers array is required", "status": "error"}

        logger.info(f"Performing {operation} on {numbers}")

        try:
            result = {}

            if operation == "mean" or operation == "all":
                result["mean"] = statistics.mean(numbers)

            if operation == "median" or operation == "all":
                result["median"] = statistics.median(numbers)

            if operation == "mode" or operation == "all":
                try:
                    result["mode"] = statistics.mode(numbers)
                except statistics.StatisticsError:
                    result["mode"] = "No unique mode found"

            if operation == "stdev" or operation == "all":
                if len(numbers) > 1:
                    result["stdev"] = statistics.stdev(numbers)
                else:
                    result["stdev"] = "Not enough data points"

            if operation == "variance" or operation == "all":
                if len(numbers) > 1:
                    result["variance"] = statistics.variance(numbers)
                else:
                    result["variance"] = "Not enough data points"

            if operation == "all":
                result["min"] = min(numbers)
                result["max"] = max(numbers)
                result["range"] = max(numbers) - min(numbers)
                result["sum"] = sum(numbers)
                result["count"] = len(numbers)

            return {
                "result": result,
                "numbers": numbers,
                "operation": operation,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error performing statistical calculation: {str(e)}")
            return {
                "error": str(e),
                "numbers": numbers,
                "operation": operation,
                "status": "error",
            }

    async def convert_units(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert between different units of measurement.

        Args:
            data: Dictionary containing the value, from_unit, to_unit, and unit_type

        Returns:
            Result of the unit conversion
        """
        value = data.get("value", 0)
        from_unit = data.get("from_unit", "")
        to_unit = data.get("to_unit", "")
        unit_type = data.get("unit_type", "")

        if not all([from_unit, to_unit]):
            return {
                "error": "Both from_unit and to_unit are required",
                "status": "error",
            }

        logger.info(f"Converting {value} from {from_unit} to {to_unit}")

        try:
            # Define conversion factors for different unit types
            conversion_factors = {
                "length": {
                    "m": 1.0,  # meter (base unit)
                    "km": 1000.0,  # kilometer
                    "cm": 0.01,  # centimeter
                    "mm": 0.001,  # millimeter
                    "in": 0.0254,  # inch
                    "ft": 0.3048,  # foot
                    "yd": 0.9144,  # yard
                    "mi": 1609.34,  # mile
                },
                "mass": {
                    "g": 1.0,  # gram (base unit)
                    "kg": 1000.0,  # kilogram
                    "mg": 0.001,  # milligram
                    "lb": 453.592,  # pound
                    "oz": 28.3495,  # ounce
                },
                "volume": {
                    "l": 1.0,  # liter (base unit)
                    "ml": 0.001,  # milliliter
                    "gal": 3.78541,  # gallon (US)
                    "qt": 0.946353,  # quart (US)
                    "pt": 0.473176,  # pint (US)
                    "c": 0.236588,  # cup (US)
                    "tbsp": 0.0147868,  # tablespoon (US)
                    "tsp": 0.00492892,  # teaspoon (US)
                },
                "temperature": {
                    "c": "celsius",  # Celsius
                    "f": "fahrenheit",  # Fahrenheit
                    "k": "kelvin",  # Kelvin
                },
                "time": {
                    "s": 1.0,  # second (base unit)
                    "ms": 0.001,  # millisecond
                    "min": 60.0,  # minute
                    "h": 3600.0,  # hour
                    "d": 86400.0,  # day
                    "w": 604800.0,  # week
                    "mo": 2592000.0,  # month (30 days)
                    "y": 31536000.0,  # year (365 days)
                },
                "area": {
                    "m2": 1.0,  # square meter (base unit)
                    "cm2": 0.0001,  # square centimeter
                    "km2": 1000000.0,  # square kilometer
                    "in2": 0.00064516,  # square inch
                    "ft2": 0.092903,  # square foot
                    "ac": 4046.86,  # acre
                    "ha": 10000.0,  # hectare
                },
                "speed": {
                    "mps": 1.0,  # meters per second (base unit)
                    "kph": 0.277778,  # kilometers per hour
                    "mph": 0.44704,  # miles per hour
                    "fps": 0.3048,  # feet per second
                    "knot": 0.514444,  # knot
                },
            }

            # Special case for temperature conversions
            if unit_type == "temperature" or (
                unit_type == ""
                and from_unit in ["c", "f", "k"]
                and to_unit in ["c", "f", "k"]
            ):
                # Convert the input value to Celsius as an intermediate step
                if from_unit.lower() == "f":
                    # Fahrenheit to Celsius: (F - 32) * 5/9
                    celsius = (value - 32) * 5 / 9
                elif from_unit.lower() == "k":
                    # Kelvin to Celsius: K - 273.15
                    celsius = value - 273.15
                else:
                    # Already in Celsius
                    celsius = value

                # Convert from Celsius to the target unit
                if to_unit.lower() == "f":
                    # Celsius to Fahrenheit: (C * 9/5) + 32
                    converted_value = (celsius * 9 / 5) + 32
                elif to_unit.lower() == "k":
                    # Celsius to Kelvin: C + 273.15
                    converted_value = celsius + 273.15
                else:
                    # Target is already Celsius
                    converted_value = celsius

                return {
                    "result": converted_value,
                    "value": value,
                    "from_unit": from_unit,
                    "to_unit": to_unit,
                    "unit_type": "temperature",
                    "status": "success",
                }

            # For other unit types, determine the unit type if not provided
            if not unit_type:
                for ut, units in conversion_factors.items():
                    if from_unit.lower() in units and to_unit.lower() in units:
                        unit_type = ut
                        break

            if not unit_type or unit_type not in conversion_factors:
                return {
                    "error": f"Cannot determine unit type for {from_unit} to {to_unit}",
                    "status": "error",
                }

            # Check if units exist in the conversion table
            if from_unit.lower() not in conversion_factors[unit_type]:
                return {"error": f"Unknown unit: {from_unit}", "status": "error"}

            if to_unit.lower() not in conversion_factors[unit_type]:
                return {"error": f"Unknown unit: {to_unit}", "status": "error"}

            # Perform the conversion
            # First convert to the base unit, then to the target unit
            base_value = value * conversion_factors[unit_type][from_unit.lower()]
            converted_value = (
                base_value / conversion_factors[unit_type][to_unit.lower()]
            )

            return {
                "result": converted_value,
                "value": value,
                "from_unit": from_unit,
                "to_unit": to_unit,
                "unit_type": unit_type,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error converting units: {str(e)}")
            return {"error": str(e), "status": "error"}

    async def finance_calc(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform financial calculations.

        Args:
            data: Dictionary containing the operation and financial parameters

        Returns:
            Result of the financial calculation
        """
        operation = data.get("operation", "")
        principal = data.get("principal", 0)
        rate = data.get("rate", 0)
        time = data.get("time", 0)
        periods = data.get("periods", 1)

        if not operation:
            return {"error": "Operation is required", "status": "error"}

        logger.info(f"Performing financial calculation: {operation}")

        try:
            result = 0

            if operation == "compound_interest":
                # Compound interest: A = P(1 + r/n)^(nt)
                result = principal * (1 + rate / periods) ** (periods * time)

            elif operation == "loan_payment":
                # Monthly payment: P = (Pv * r/12) / (1 - (1 + r/12)^(-n))
                if rate == 0:
                    result = principal / (time * 12)
                else:
                    monthly_rate = rate / 12
                    num_payments = time * 12
                    result = (principal * monthly_rate) / (
                        1 - (1 + monthly_rate) ** (-num_payments)
                    )

            elif operation == "present_value":
                # Present value: PV = FV / (1 + r)^t
                result = principal / ((1 + rate) ** time)

            elif operation == "future_value":
                # Future value: FV = PV(1 + r)^t
                result = principal * ((1 + rate) ** time)

            else:
                return {"error": f"Unknown operation: {operation}", "status": "error"}

            return {
                "result": result,
                "operation": operation,
                "principal": principal,
                "rate": rate,
                "time": time,
                "periods": periods,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error performing financial calculation: {str(e)}")
            return {"error": str(e), "status": "error"}

    async def start(self):
        """Start the math agent server."""
        await self.server.start_server()
        logger.info(f"Math agent started on {self.host}:{self.port}")

    async def close(self):
        """Stop the math agent server."""
        await self.server.close()
        logger.info("Math agent stopped")


async def main():
    """Main function for the math agent."""
    parser = argparse.ArgumentParser(description="A2A Network Math Agent")
    parser.add_argument("--host", default="localhost", help="Host to bind the server")
    parser.add_argument(
        "--port", type=int, default=8082, help="Port to bind the server"
    )

    args = parser.parse_args()

    # Create and start the math agent
    math_agent = MathAgent(host=args.host, port=args.port)

    try:
        await math_agent.start()

        # Keep the server running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping server...")

    finally:
        await math_agent.close()


if __name__ == "__main__":
    asyncio.run(main())
