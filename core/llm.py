"""
Nexus — LLM Client wrapping AWS Bedrock Converse API.

Provides invoke (plain text) and invoke_with_tools (tool-calling) methods.
Default model: Amazon Nova Pro.

Implements: blueprints/core/llm.spec.md
"""
import json
import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from core.types import LLMResponse, Message, ToolCall

logger = logging.getLogger(__name__)


class LLMClient:
    """Bedrock Converse API client for Amazon Nova Pro."""

    def __init__(self, model_id: str = "amazon.nova-pro-v1:0", region: str = "us-east-1"):
        self.model_id = model_id
        self.region = region
        try:
            self.client = boto3.client("bedrock-runtime", region_name=region)
            logger.info(f"LLM client initialized: model={model_id}, region={region}")
        except NoCredentialsError:
            raise RuntimeError(
                "AWS credentials not found. Configure via environment variables "
                "(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or ~/.aws/credentials"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize AWS Bedrock client: {e}\n"
                "If you see a MissingDependencyException, run: pip install 'botocore[crt]'"
            )

    def invoke(self, messages: List[Message], system_prompt: str = "") -> LLMResponse:
        """Plain conversation — text in, text out."""
        bedrock_messages = self._convert_messages(messages)
        system = [{"text": system_prompt}] if system_prompt else None

        try:
            kwargs: Dict[str, Any] = {
                "modelId": self.model_id,
                "messages": bedrock_messages,
            }
            if system:
                kwargs["system"] = system

            response = self.client.converse(**kwargs)
            return self._parse_response(response)

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise RuntimeError(f"LLM invocation failed: {e}")

    def invoke_with_tools(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List,
    ) -> LLMResponse:
        """Conversation with tool definitions for function calling."""
        bedrock_messages = self._convert_messages(messages)
        system = [{"text": system_prompt}] if system_prompt else None
        tool_config = self._build_tool_config(tools)

        try:
            kwargs: Dict[str, Any] = {
                "modelId": self.model_id,
                "messages": bedrock_messages,
            }
            if system:
                kwargs["system"] = system
            if tool_config:
                kwargs["toolConfig"] = tool_config

            response = self.client.converse(**kwargs)
            return self._parse_response(response)

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise RuntimeError(f"LLM invocation with tools failed: {e}")

    def invoke_with_tools_raw(
        self,
        bedrock_messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: List,
    ) -> LLMResponse:
        """Conversation with tools using pre-formatted Bedrock messages.

        Unlike invoke_with_tools, this accepts messages already in Bedrock
        Converse API format. Used by graph nodes that manage the tool-use
        loop and need to append raw tool result messages.
        """
        system = [{"text": system_prompt}] if system_prompt else None
        tool_config = self._build_tool_config(tools)

        try:
            kwargs: Dict[str, Any] = {
                "modelId": self.model_id,
                "messages": bedrock_messages,
            }
            if system:
                kwargs["system"] = system
            if tool_config:
                kwargs["toolConfig"] = tool_config

            response = self.client.converse(**kwargs)
            return self._parse_response(response)

        except ClientError as e:
            logger.error(f"Bedrock API error: {e}")
            raise RuntimeError(f"LLM invocation with tools (raw) failed: {e}")

    def format_tool_result(self, tool_use_id: str, result: str) -> Dict[str, Any]:
        """Create a tool result message to feed back to the LLM."""
        return {
            "role": "user",
            "content": [
                {
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": result}],
                    }
                }
            ],
        }

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message list to Bedrock Converse API format."""
        bedrock_messages = []
        for msg in messages:
            if msg.role == "system":
                continue  # System messages are handled separately
            if msg.role == "tool":
                # Tool results use special format
                tool_use_id = msg.metadata.get("tool_use_id", "")
                bedrock_messages.append({
                    "role": "user",
                    "content": [{
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [{"text": msg.content}],
                        }
                    }],
                })
            else:
                bedrock_messages.append({
                    "role": msg.role,
                    "content": [{"text": msg.content}],
                })
        return bedrock_messages

    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
        """Parse Bedrock Converse API response into LLMResponse."""
        output = response.get("output", {})
        message = output.get("message", {})
        content_blocks = message.get("content", [])

        text = ""
        tool_call = None

        for block in content_blocks:
            if "text" in block:
                text += block["text"]
            elif "toolUse" in block:
                tu = block["toolUse"]
                tool_call = ToolCall(
                    name=tu.get("name", ""),
                    arguments=tu.get("input", {}),
                    tool_use_id=tu.get("toolUseId", ""),
                )

        # Extract reasoning from text if present (between <reasoning> tags)
        reasoning = ""
        if "<reasoning>" in text and "</reasoning>" in text:
            import re
            match = re.search(r"<reasoning>(.*?)</reasoning>", text, re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                # Remove reasoning tags from visible text
                text = re.sub(r"<reasoning>.*?</reasoning>\s*", "", text, flags=re.DOTALL).strip()

        return LLMResponse(
            text=text,
            tool_call=tool_call,
            reasoning=reasoning,
            raw_response=response,
        )

    def _build_tool_config(self, tools: List) -> Optional[Dict[str, Any]]:
        """Convert tool definitions to Bedrock toolConfig format.

        Supports both:
        - LangChain @tool decorated functions (have .name, .description, .args_schema)
        - Plain dicts with name, description, input_schema
        """
        if not tools:
            return None

        tool_specs = []
        for t in tools:
            if isinstance(t, dict):
                tool_specs.append({"toolSpec": t})
            elif hasattr(t, "name") and hasattr(t, "description"):
                # LangChain @tool decorated function
                schema = {}
                if hasattr(t, "args_schema") and t.args_schema:
                    schema = t.args_schema.schema()
                elif hasattr(t, "args"):
                    schema = {
                        "type": "object",
                        "properties": {
                            k: {"type": "string", "description": v.get("description", "")}
                            for k, v in t.args.items()
                        },
                        "required": list(t.args.keys()),
                    }

                tool_specs.append({
                    "toolSpec": {
                        "name": t.name,
                        "description": t.description,
                        "inputSchema": {"json": schema},
                    }
                })
            else:
                logger.warning(f"Unknown tool format: {type(t)}, skipping")

        return {"tools": tool_specs} if tool_specs else None
