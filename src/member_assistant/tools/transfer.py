"""Idempotent mock internal-transfer adapter."""

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import threading
from typing import Any, Dict

from .accounts import MockAccountTool


@dataclass(frozen=True)
class TransferRequest:
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    idempotency_key: str


@dataclass(frozen=True)
class TransferReceipt:
    transaction_id: str
    status: str
    source_account_id: str
    destination_account_id: str
    amount: Decimal
    duplicate: bool = False


class MockTransferTool:
    name = "mock_internal_transfer"
    actions = ("submit",)

    def __init__(self, accounts: MockAccountTool):
        self.accounts = accounts
        self._receipts: Dict[str, TransferReceipt] = {}
        self._lock = threading.Lock()

    @property
    def submission_count(self) -> int:
        return len(self._receipts)

    def submit(self, request: TransferRequest) -> TransferReceipt:
        with self._lock:
            existing = self._receipts.get(request.idempotency_key)
            if existing:
                return TransferReceipt(
                    transaction_id=existing.transaction_id,
                    status=existing.status,
                    source_account_id=existing.source_account_id,
                    destination_account_id=existing.destination_account_id,
                    amount=existing.amount,
                    duplicate=True,
                )
            digest = hashlib.sha256(request.idempotency_key.encode("utf-8")).hexdigest()[:10]
            receipt = TransferReceipt(
                transaction_id="MOCK-{}".format(digest.upper()),
                status="completed",
                source_account_id=request.source_account_id,
                destination_account_id=request.destination_account_id,
                amount=request.amount,
            )
            self._receipts[request.idempotency_key] = receipt
            return receipt

    def invoke(self, action: str, arguments: Dict[str, Any]) -> Any:
        if action != "submit":
            raise ValueError("Unsupported mock transfer action: {}".format(action))
        receipt = self.submit(
            TransferRequest(
                source_account_id=str(arguments["source_account_id"]),
                destination_account_id=str(arguments["destination_account_id"]),
                amount=Decimal(str(arguments["amount"])),
                idempotency_key=str(arguments["idempotency_key"]),
            )
        )
        return {
            "transaction_id": receipt.transaction_id,
            "status": receipt.status,
            "source_account_id": receipt.source_account_id,
            "destination_account_id": receipt.destination_account_id,
            "amount": format(receipt.amount, ".2f"),
            "duplicate": receipt.duplicate,
        }
