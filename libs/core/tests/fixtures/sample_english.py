"""Sample English Python code for testing translation.

This file contains realistic Python code with various features:
- Functions and classes
- Control flow (if/for/while)
- Exception handling
- Type hints
- Comments and docstrings
"""


def calculate_tax(income: float, rate: float) -> float:
    """Calculate income tax based on income and rate.

    Args:
        income: Annual income amount
        rate: Tax rate as decimal (e.g., 0.25 for 25%)

    Returns:
        Tax amount owed
    """
    if income <= 0:
        return 0.0
    elif income > 1000000:
        # High earners pay higher rate
        return income * (rate + 0.1)
    else:
        return income * rate


class BankAccount:
    """Simple bank account class."""

    def __init__(self, balance: float = 0):
        """Initialize account with optional starting balance."""
        self.balance = balance

    def deposit(self, amount: float) -> None:
        """Add money to account."""
        if amount > 0:
            self.balance += amount
        else:
            raise ValueError("Deposit amount must be positive")

    def withdraw(self, amount: float) -> bool:
        """Remove money from account.

        Returns:
            True if withdrawal successful, False if insufficient funds
        """
        if amount > self.balance:
            return False
        else:
            self.balance -= amount
            return True

    def get_balance(self) -> float:
        """Return current balance."""
        return self.balance


def process_transactions(transactions: list) -> dict:
    """Process a list of banking transactions.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        Summary of processed transactions
    """
    total_deposits = 0
    total_withdrawals = 0

    for transaction in transactions:
        try:
            if transaction["type"] == "deposit":
                total_deposits += transaction["amount"]
            elif transaction["type"] == "withdrawal":
                total_withdrawals += transaction["amount"]
            else:
                print(f"Unknown transaction type: {transaction['type']}")

        except KeyError as e:
            print(f"Invalid transaction format: {e}")
            continue

    return {
        "deposits": total_deposits,
        "withdrawals": total_withdrawals,
        "net": total_deposits - total_withdrawals,
    }


async def fetch_account_data(account_id: int):
    """Asynchronously fetch account data from API."""
    import asyncio

    # Simulated async operation
    await asyncio.sleep(1)
    return {"id": account_id, "balance": 1000.0}


def main():
    """Main entry point for the application."""
    # Create account
    account = BankAccount(balance=1000.0)

    # Process some transactions
    account.deposit(500)
    account.withdraw(200)

    # Display balance
    print(f"Current balance: ${account.get_balance():.2f}")

    # Process batch transactions
    transactions = [
        {"type": "deposit", "amount": 100},
        {"type": "withdrawal", "amount": 50},
        {"type": "deposit", "amount": 200},
    ]

    summary = process_transactions(transactions)
    print(f"Transaction summary: {summary}")


if __name__ == "__main__":
    main()
