"""Mock insurance tools for development and testing."""


class FileClaim:
    name = "file_claim"
    description = "File a new insurance claim"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The policy holder's user ID"},
            "claim_type": {
                "type": "string",
                "enum": ["auto", "home", "health"],
                "description": "Type of claim",
            },
            "description": {"type": "string", "description": "Description of the incident"},
        },
        "required": ["user_id", "claim_type"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "claim_id": "CLM-2026-00389",
            "claim_type": args.get("claim_type", "auto"),
            "estimated_processing_time": "5-7 business days",
            "message": "Claim filed successfully. You will receive updates via email.",
        }


class CheckClaimStatus:
    name = "check_claim_status"
    description = "Check the status of an existing insurance claim"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The policy holder's user ID"},
            "claim_id": {"type": "string", "description": "The claim ID to check"},
        },
        "required": ["user_id"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "claim_id": args.get("claim_id", "CLM-2026-00389"),
            "claim_status": "Under Review",
            "last_updated": "2026-04-07",
            "estimated_completion": "2026-04-14",
        }


class GetPolicyDetails:
    name = "get_policy_details"
    description = "Retrieve details of an existing insurance policy"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The policy holder's user ID"},
            "policy_type": {"type": "string", "enum": ["auto", "home", "health"]},
        },
        "required": ["user_id"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "policy_id": "POL-AUTO-78234",
            "policy_type": args.get("policy_type", "auto"),
            "coverage": "$100,000",
            "deductible": "$500",
            "premium": "$125/month",
            "renewal_date": "2026-09-15",
        }


class RequestQuote:
    name = "request_quote"
    description = "Request an insurance quote"
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "The customer's user ID"},
            "insurance_type": {"type": "string", "enum": ["auto", "home", "health"]},
        },
        "required": ["insurance_type"],
    }

    def execute(self, args: dict) -> dict:
        return {
            "status": "success",
            "insurance_type": args.get("insurance_type", "auto"),
            "estimated_premium": "$110/month",
            "coverage_options": ["Basic", "Standard", "Premium"],
            "message": "Quote generated. An agent will follow up within 24 hours.",
        }


def register_insurance_tools(registry) -> None:
    """Register all insurance tools with the given registry."""
    for tool_cls in [FileClaim, CheckClaimStatus, GetPolicyDetails, RequestQuote]:
        registry.register(tool_cls())
