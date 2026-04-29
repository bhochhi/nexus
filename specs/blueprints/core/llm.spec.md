# Spec: LLM Client

## Purpose
Wraps the AWS Bedrock Converse API to provide a simple interface for LLM invocations. Supports both plain conversation (text in, text out) and tool-augmented conversation (text in, text or tool-call out). Uses Amazon Nova Pro as the default model.

## Interface Contract

### `class LLMClient`

#### `__init__(self, model_id: str = "amazon.nova-pro-v1:0", region: str = "us-east-1")`
- Create a `boto3` Bedrock Runtime client
- Store model_id and region for all subsequent calls
- Should handle missing AWS credentials gracefully (raise clear error)

#### `invoke(self, messages: List[Message], system_prompt: str = "") -> LLMResponse`
- Plain conversation — no tools
- Convert `Message` list to Bedrock Converse API format
- Include `system_prompt` as system message if provided
- Call Bedrock `converse()` API
- Return `LLMResponse` with `text` populated, `tool_call=None`
- Extract reasoning from the response text for the debug panel

#### `invoke_with_tools(self, messages: List[Message], system_prompt: str, tools: List) -> LLMResponse`
- Conversation with tool definitions
- `tools` is a list of LangChain `@tool`-decorated functions
- Convert tool definitions to Bedrock `toolConfig` format
- Call Bedrock `converse()` API with tool configuration
- If LLM responds with text: return `LLMResponse(text=..., tool_call=None)`
- If LLM responds with tool_use: return `LLMResponse(text="", tool_call=ToolCall(...))`
- Extract reasoning from response for debug panel

#### `format_tool_result(self, tool_use_id: str, result: str) -> Message`
- Create a tool result message to feed back to the LLM
- Used after executing a tool call to get the LLM's final response

### Bedrock Converse API Format

```python
# Message format for Bedrock Converse API:
{
    "role": "user" | "assistant",
    "content": [{"text": "..."}]
}

# System prompt format:
[{"text": "system prompt content"}]

# Tool config format:
{
    "tools": [{
        "toolSpec": {
            "name": "tool_name",
            "description": "what the tool does",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": { ... },
                    "required": [ ... ]
                }
            }
        }
    }]
}

# Tool use response (from LLM):
{
    "role": "assistant",
    "content": [{
        "toolUse": {
            "toolUseId": "unique-id",
            "name": "tool_name",
            "input": { "arg1": "value1" }
        }
    }]
}

# Tool result message (fed back to LLM):
{
    "role": "user",
    "content": [{
        "toolResult": {
            "toolUseId": "unique-id",
            "content": [{"text": "result text"}]
        }
    }]
}
```

## Acceptance Criteria

- [ ] `LLMClient` initializes with default model_id and region
- [ ] `invoke` sends messages and returns text response
- [ ] `invoke_with_tools` sends messages with tool definitions
- [ ] When LLM returns text, `LLMResponse.tool_call` is None
- [ ] When LLM returns tool_use, `LLMResponse.tool_call` is populated with name, arguments, tool_use_id
- [ ] `LLMResponse.reasoning` is populated for the debug panel
- [ ] System prompt is included when provided
- [ ] Empty system prompt is handled gracefully (not sent)
- [ ] `format_tool_result` creates properly formatted tool result message
- [ ] Missing AWS credentials raise a clear, descriptive error
- [ ] Bedrock API errors are caught and wrapped with context
- [ ] Message conversion handles all roles: user, assistant, system, tool

## Examples

```python
client = LLMClient()

# Plain conversation
messages = [Message(role="user", content="Hello!")]
response = client.invoke(messages, system_prompt="You are a helpful assistant.")
assert response.text != ""
assert response.tool_call is None

# With tools
@tool
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"

response = client.invoke_with_tools(messages, system_prompt="...", tools=[greet])
# LLM may return text OR a tool call
if response.tool_call:
    assert response.tool_call.name == "greet"
    assert "name" in response.tool_call.arguments
```

## Dependencies
- `boto3` (AWS SDK)
- `core.types` (Message, LLMResponse, ToolCall)

## Notes
- The `reasoning` field in LLMResponse is extracted from the LLM's response text. We instruct the LLM (via system prompt) to include its reasoning in a structured way, then parse it out. Alternative: use a `<reasoning>` XML tag in the system prompt for easy extraction.
- Tool schema conversion from LangChain `@tool` format to Bedrock `toolSpec` format will need an adapter function.
