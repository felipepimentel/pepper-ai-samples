"""Fraud Detection MCP Server."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from pepperpy_mcp.server.fastmcp import Context, FastMCP


@dataclass
class Transaction:
    """Transaction data class."""

    id: str
    amount: float
    timestamp: datetime
    merchant: str
    card_id: str
    location: str


class FraudDetector:
    """Simple fraud detection system."""

    def __init__(self):
        self.transactions: List[Transaction] = []
        self.rules = {"amount_threshold": 1000.0, "location_change_threshold_hours": 2}

    def add_transaction(self, transaction: Transaction) -> None:
        """Add a transaction to the system."""
        self.transactions.append(transaction)

    def check_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """Check a transaction for potential fraud."""
        alerts = []

        # Check amount threshold
        if transaction.amount > self.rules["amount_threshold"]:
            alerts.append(
                {
                    "type": "high_amount",
                    "details": f"Amount ${transaction.amount} exceeds threshold ${self.rules['amount_threshold']}",
                }
            )

        # Check for rapid location change
        recent_transactions = [
            t
            for t in self.transactions
            if t.card_id == transaction.card_id
            and (transaction.timestamp - t.timestamp).total_seconds() / 3600
            < self.rules["location_change_threshold_hours"]
        ]

        if recent_transactions:
            last_location = recent_transactions[-1].location
            if last_location != transaction.location:
                alerts.append(
                    {
                        "type": "rapid_location_change",
                        "details": f"Location changed from {last_location} to {transaction.location} in less than {self.rules['location_change_threshold_hours']} hours",
                    }
                )

        return {
            "transaction_id": transaction.id,
            "risk_level": "high" if alerts else "low",
            "alerts": alerts,
        }


# Create an MCP server
mcp = FastMCP("Fraud Detection")


@mcp.tool()
async def analyze_transaction(
    transaction_data: Dict[str, Any], ctx: Context
) -> Dict[str, Any]:
    """Analyze a transaction for potential fraud."""
    try:
        # Create transaction object
        transaction = Transaction(
            id=transaction_data["id"],
            amount=float(transaction_data["amount"]),
            timestamp=datetime.fromisoformat(transaction_data["timestamp"]),
            merchant=transaction_data["merchant"],
            card_id=transaction_data["card_id"],
            location=transaction_data["location"],
        )

        # Initialize detector
        detector = FraudDetector()

        # Add some example historical transactions
        detector.add_transaction(
            Transaction(
                "prev1",
                50.0,
                datetime.fromisoformat("2025-04-10T10:00:00"),
                "Store A",
                transaction.card_id,
                "New York",
            )
        )

        # Analyze transaction
        result = detector.check_transaction(transaction)
        await ctx.info(
            f"Analyzed transaction {transaction.id}: Risk level {result['risk_level']}"
        )
        return result

    except Exception as e:
        await ctx.error(f"Analysis error: {e}")
        return {"error": str(e)}


@mcp.resource("rules://fraud")
def get_fraud_rules() -> Dict[str, Any]:
    """Get current fraud detection rules."""
    detector = FraudDetector()
    return detector.rules


if __name__ == "__main__":
    mcp.run()
