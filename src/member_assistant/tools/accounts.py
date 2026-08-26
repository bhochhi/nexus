"""Mock account data adapter."""

from dataclasses import dataclass
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AccountBalance:
    account_id: str
    account_type: str
    masked_number: str
    available_balance: Decimal
    currency: str = "USD"

    @property
    def label(self) -> str:
        return "{} ending in {}".format(self.account_type.title(), self.masked_number[-4:])


class MockAccountTool:
    name = "mock_accounts"
    actions = ("list_eligible_balances", "resolve_account")

    def __init__(self):
        self._accounts = [
            AccountBalance("chk-001", "checking", "••••1001", Decimal("2450.75")),
            AccountBalance("sav-001", "savings", "••••2002", Decimal("8250.25")),
        ]

    def list_eligible_balances(self, member_ref: str) -> List[AccountBalance]:
        # member_ref is a synthetic POC identifier, never real member data.
        return list(self._accounts)

    def resolve(self, reference: str) -> Optional[AccountBalance]:
        normalized = " ".join(re.findall(r"[a-z0-9]+", reference.lower()))
        tokens = set(normalized.split())
        if "saving" in tokens:
            tokens.add("savings")
        for account in self._accounts:
            candidates = {
                account.account_id,
                account.account_type,
                account.masked_number[-4:],
                account.label.lower(),
            }
            normalized_candidates = {
                " ".join(re.findall(r"[a-z0-9]+", candidate.lower()))
                for candidate in candidates
            }
            if normalized in normalized_candidates or any(
                set(candidate.split()).issubset(tokens)
                for candidate in normalized_candidates
                if candidate
            ):
                return account
        return None

    def invoke(self, action: str, arguments: Dict[str, Any]) -> Any:
        if action == "list_eligible_balances":
            return [
                self._as_contract(account)
                for account in self.list_eligible_balances(str(arguments["member_ref"]))
            ]
        if action == "resolve_account":
            account = self.resolve(str(arguments["reference"]))
            return self._as_contract(account) if account else None
        raise ValueError("Unsupported mock account action: {}".format(action))

    @staticmethod
    def _as_contract(account: AccountBalance) -> Dict[str, Any]:
        return {
            "account_id": account.account_id,
            "account_type": account.account_type,
            "masked_number": account.masked_number,
            "available_balance": format(account.available_balance, ",.2f"),
            "currency": account.currency,
            "label": account.label,
            "aliases": [
                account.account_id,
                account.account_type,
                account.masked_number[-4:],
                account.label,
            ],
        }
