"""FAQ tool for answering general questions."""


class AnswerFAQ:
    name = "answer_faq"
    description = "Answer frequently asked questions about the organization"
    parameters = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The user's question"},
        },
        "required": ["question"],
    }

    FAQ_DATA = {
        "hours_of_operation": "We are open Monday-Friday 8am-6pm EST, Saturday 9am-1pm EST.",
        "contact_support": "Call us at 1-800-555-0199 or email support@nexus-financial.com.",
        "reset_password": "Visit nexus-financial.com/reset or call support to reset your password.",
        "fees_info": "Checking accounts have no monthly fee. Wire transfers cost $25 domestic.",
        "locations": "Find branches and ATMs at nexus-financial.com/locations.",
        "security_info": "We use 256-bit encryption, MFA, and 24/7 fraud monitoring.",
    }

    def execute(self, args: dict) -> dict:
        question = args.get("question", "")
        for key, answer in self.FAQ_DATA.items():
            if key.replace("_", " ") in question.lower():
                return {"status": "success", "answer": answer}
        return {
            "status": "success",
            "answer": "Please visit nexus-financial.com or call 1-800-555-0199.",
        }


def register_faq_tools(registry) -> None:
    """Register FAQ tools with the given registry."""
    registry.register(AnswerFAQ())
