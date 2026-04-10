"""Mock banking tools for development and testing."""


class GetAccountBalance:
    name = "get_account_balance"
    description = "Retrieve the current balance for a user's bank account"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The customer's user ID"},
            "account_type": {
                "type": "string",
                "enum": ["checking", "savings"],
                "description": "Type of account",
            },
        },
        "required": ["user_id"],
    }

    def execute(self, args: dict) -> dict:
        account_type = args.get("account_type", "checking")
        return {
            "status": "success",
            "account_type": account_type,
            "balance": 4250.75 if account_type == "checking" else 12800.50,
            "currency": "USD",
            "account_number": "****4521",
        }


class TransferFunds:
    name = "transfer_funds"
    description = "Transfer funds between accounts or to another person"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The customer's user ID"},
            "from_account": {"type": "string", "description": "Source account type"},
            "to_account": {"type": "string", "description": "Destination account or recipient"},
            "amount": {"type": "number", "description": "Amount to transfer"},
        },
        "required": ["user_id", "from_account", "to_account", "amount"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "transfer_id": "TXN-20260409-001",
            "amount": args.get("amount", 0),
            "from_account": args.get("from_account", "checking"),
            "to_account": args.get("to_account", "savings"),
            "message": "Transfer completed successfully",
        }


class GetTransactions:
    name = "get_transactions"
    description = "Retrieve recent transaction history"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The customer's user ID"},
            "limit": {"type": "integer", "description": "Number of transactions to return"},
        },
        "required": ["user_id"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "transactions": [
                {"date": "2026-04-08", "description": "Grocery Store", "amount": -67.43},
                {"date": "2026-04-07", "description": "Direct Deposit", "amount": 2500.00},
                {"date": "2026-04-06", "description": "Electric Bill", "amount": -125.80},
            ],
        }


class ReportFraud:
    name = "report_fraud"
    description = "Report a fraudulent or suspicious transaction"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The customer's user ID"},
            "transaction_description": {
                "type": "string",
                "description": "Description of the suspicious transaction",
            },
        },
        "required": ["user_id"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "case_id": "FRD-2026-00142",
            "message": "Fraud report filed. Your card has been temporarily frozen.",
        }


class FreezeCard:
    name = "freeze_card"
    description = "Temporarily freeze a debit or credit card"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The customer's user ID"},
            "card_type": {"type": "string", "enum": ["debit", "credit"]},
        },
        "required": ["user_id"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "card_type": args.get("card_type", "debit"),
            "message": "Card has been frozen. You can unfreeze it anytime.",
        }


def register_banking_tools(registry) -> None:
    """Register all banking tools with the given registry."""
    for tool_cls in [GetAccountBalance, TransferFunds, GetTransactions, ReportFraud, FreezeCard]:
        registry.register(tool_cls())
