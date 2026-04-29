"""
Nexus — LLM Client Interface and Implementations.

Provides provider-agnostic invoke and invoke_with_tools methods.
Supports AWS Bedrock (Nova Pro) and OpenAI (GPT-4o).

Implements: blueprints/core/llm.spec.md
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
try:
    import openai
except ImportError:
    openai = None

from core.types import LLMResponse, Message, ToolCall

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract interface for LLM clients."""

    @abstractmethod
    def invoke(self, messages: List[Message], system_prompt: str = "") -> LLMResponse:
        """Plain conversation — text in, text out."""
        ...

    @abstractmethod
    def invoke_with_tools(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List,
    ) -> LLMResponse:
        """Conversation with tool definitions for function calling."""
        ...


class BedrockLLMClient(LLMClient):
    """Bedrock Converse API client for Amazon Nova Pro."""

    def __init__(self, model_id: str = "amazon.nova-pro-v1:0", region: str = "us-east-1"):
        self.model_id = model_id
        self.region = region
        try:
            self.client = boto3.client("bedrock-runtime", region_name=region)
            logger.info(f"Bedrock LLM client initialized: model={model_id}, region={region}")
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

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert standard Messages to Bedrock Converse API format."""
        bedrock_messages = []
        for msg in messages:
            if msg.role == "system":
                continue

            if msg.role == "tool":
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
            elif msg.role == "assistant":
                content_blocks = []
                if msg.content:
                    content_blocks.append({"text": msg.content})
                
                tool_calls = msg.metadata.get("tool_calls", [])
                for tc in tool_calls:
                    content_blocks.append({
                        "toolUse": {
                            "toolUseId": tc.tool_use_id,
                            "name": tc.name,
                            "input": tc.arguments,
                        }
                    })
                
                if content_blocks:
                    bedrock_messages.append({
                        "role": "assistant",
                        "content": content_blocks,
                    })
            else:
                bedrock_messages.append({
                    "role": msg.role,
                    "content": [{"text": msg.content}],
                })
        return bedrock_messages

    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
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

        reasoning = ""
        if "<reasoning>" in text and "</reasoning>" in text:
            import re
            match = re.search(r"<reasoning>(.*?)</reasoning>", text, re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                text = re.sub(r"<reasoning>.*?</reasoning>\s*", "", text, flags=re.DOTALL).strip()

        return LLMResponse(
            text=text,
            tool_call=tool_call,
            reasoning=reasoning,
            raw_response=response,
        )

    def _build_tool_config(self, tools: List) -> Optional[Dict[str, Any]]:
        if not tools:
            return None

        tool_specs = []
        for t in tools:
            if isinstance(t, dict):
                tool_specs.append({"toolSpec": t})
            elif hasattr(t, "name") and hasattr(t, "description"):
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


class OpenAILLMClient(LLMClient):
    """OpenAI API client for GPT-4o."""

    def __init__(self, api_key: str, model_id: str = "gpt-4o"):
        if not openai:
            raise RuntimeError("openai package is not installed. Run: pip install openai")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")
        self.model_id = model_id
        self.client = openai.OpenAI(api_key=api_key)
        logger.info(f"OpenAI LLM client initialized: model={model_id}")

    def invoke(self, messages: List[Message], system_prompt: str = "") -> LLMResponse:
        openai_messages = self._convert_messages(messages, system_prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=openai_messages,
            )
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"LLM invocation failed: {e}")

    def invoke_with_tools(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List,
    ) -> LLMResponse:
        openai_messages = self._convert_messages(messages, system_prompt)
        openai_tools = self._build_tools(tools)

        try:
            kwargs = {
                "model": self.model_id,
                "messages": openai_messages,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools
                
            response = self.client.chat.completions.create(**kwargs)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"LLM invocation with tools failed: {e}")

    def _convert_messages(self, messages: List[Message], system_prompt: str) -> List[Dict[str, Any]]:
        openai_messages = []
        if system_prompt:
            openai_messages.append({"role": "system", "content": system_prompt})

        for msg in messages:
            if msg.role == "system":
                continue

            if msg.role == "tool":
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.metadata.get("tool_use_id", ""),
                    "content": msg.content,
                })
            elif msg.role == "assistant":
                msg_dict = {"role": "assistant"}
                if msg.content:
                    msg_dict["content"] = msg.content
                    
                tool_calls = msg.metadata.get("tool_calls", [])
                if tool_calls:
                    msg_dict["tool_calls"] = []
                    for tc in tool_calls:
                        msg_dict["tool_calls"].append({
                            "id": tc.tool_use_id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments),
                            }
                        })
                openai_messages.append(msg_dict)
            else:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        return openai_messages

    def _parse_response(self, response: Any) -> LLMResponse:
        choice = response.choices[0]
        msg = choice.message
        
        text = msg.content or ""
        tool_call = None
        
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            try:
                args = json.loads(tc.function.arguments)
            except:
                args = {}
            tool_call = ToolCall(
                name=tc.function.name,
                arguments=args,
                tool_use_id=tc.id,
            )

        # Basic reasoning extraction from text if needed (similar to Bedrock)
        reasoning = ""
        if "<reasoning>" in text and "</reasoning>" in text:
            import re
            match = re.search(r"<reasoning>(.*?)</reasoning>", text, re.DOTALL)
            if match:
                reasoning = match.group(1).strip()
                text = re.sub(r"<reasoning>.*?</reasoning>\s*", "", text, flags=re.DOTALL).strip()

        return LLMResponse(
            text=text,
            tool_call=tool_call,
            reasoning=reasoning,
            raw_response=response.model_dump(),
        )

    def _build_tools(self, tools: List) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None

        openai_tools = []
        for t in tools:
            if isinstance(t, dict):
                # If it's already a dict but formatted for Bedrock, we need to handle that,
                # but standard plain dicts should probably be openai native.
                if "toolSpec" in t: # Bedrock format
                    spec = t["toolSpec"]
                    schema = spec.get("inputSchema", {}).get("json", {})
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": spec.get("name"),
                            "description": spec.get("description"),
                            "parameters": schema
                        }
                    })
                elif "name" in t and "inputSchema" in t: # Bare bedrock format
                    schema = t.get("inputSchema", {}).get("json", {})
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": t.get("name"),
                            "description": t.get("description"),
                            "parameters": schema
                        }
                    })
                else:
                    openai_tools.append(t)
            elif hasattr(t, "name") and hasattr(t, "description"):
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

                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": schema,
                    }
                })

        return openai_tools if openai_tools else None


def get_llm_client(config) -> LLMClient:
    """Factory to get the configured LLM client."""
    provider = getattr(config, "LLM_PROVIDER", "bedrock").lower()
    if provider == "openai":
        return OpenAILLMClient(api_key=config.OPENAI_API_KEY, model_id=config.OPENAI_MODEL_ID)
    else:
        return BedrockLLMClient(model_id=config.LLM_MODEL_ID, region=config.LLM_REGION)
