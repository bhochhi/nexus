import json
import logging

import boto3

from nexus.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class BedrockLLM(BaseLLM):
    """AWS Bedrock LLM using the Converse API for Nova Pro."""

    def __init__(self, model_id: str, region: str = "us-east-1"):
        super().__init__(model_id)
        self.client = boto3.client("bedrock-runtime", region_name=region)

    def invoke(self, prompt: str, system_prompt: str | None = None) -> str:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        kwargs: dict = {"modelId": self.model_id, "messages": messages}
        if system_prompt:
            kwargs["system"] = [{"text": system_prompt}]

        response = self.client.converse(**kwargs)
        return response["output"]["message"]["content"][0]["text"]

    def invoke_with_tools(
        self,
        prompt: str,
        tools: list[dict],
        system_prompt: str | None = None,
    ) -> dict:
        messages = [{"role": "user", "content": [{"text": prompt}]}]

        tool_config = {
            "tools": [
                {
                    "toolSpec": {
                        "name": t["name"],
                        "description": t["description"],
                        "inputSchema": {"json": t["parameters"]},
                    }
                }
                for t in tools
            ]
        }

        kwargs: dict = {
            "modelId": self.model_id,
            "messages": messages,
            "toolConfig": tool_config,
        }
        if system_prompt:
            kwargs["system"] = [{"text": system_prompt}]

        response = self.client.converse(**kwargs)
        output = response["output"]["message"]["content"]

        # Parse response: may contain text, toolUse, or both
        result: dict = {"text": None, "tool_calls": []}
        for block in output:
            if "text" in block:
                result["text"] = block["text"]
            elif "toolUse" in block:
                result["tool_calls"].append(
                    {
                        "id": block["toolUse"]["toolUseId"],
                        "name": block["toolUse"]["name"],
                        "args": block["toolUse"]["input"],
                    }
                )

        # If text response looks like JSON (for routing), parse it
        if result["text"] and not result["tool_calls"]:
            try:
                result["parsed_json"] = json.loads(result["text"])
            except (json.JSONDecodeError, TypeError):
                pass

        return result
