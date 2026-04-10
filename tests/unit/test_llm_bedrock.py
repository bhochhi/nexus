from unittest.mock import MagicMock, patch

from nexus.llm.bedrock import BedrockLLM


def test_invoke_formats_request():
    with patch("nexus.llm.bedrock.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": "Hello!"}]}}
        }

        llm = BedrockLLM(model_id="amazon.nova-pro-v1:0")
        result = llm.invoke("Hi there")

        assert result == "Hello!"
        mock_client.converse.assert_called_once()
        call_kwargs = mock_client.converse.call_args[1]
        assert call_kwargs["modelId"] == "amazon.nova-pro-v1:0"
        assert call_kwargs["messages"][0]["role"] == "user"


def test_invoke_with_system_prompt():
    with patch("nexus.llm.bedrock.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.converse.return_value = {
            "output": {"message": {"content": [{"text": "Response"}]}}
        }

        llm = BedrockLLM(model_id="amazon.nova-pro-v1:0")
        llm.invoke("Hi", system_prompt="You are helpful")

        call_kwargs = mock_client.converse.call_args[1]
        assert call_kwargs["system"] == [{"text": "You are helpful"}]


def test_invoke_with_tools_parses_tool_use():
    with patch("nexus.llm.bedrock.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.converse.return_value = {
            "output": {
                "message": {
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-1",
                                "name": "get_balance",
                                "input": {"user_id": "123"},
                            }
                        }
                    ]
                }
            }
        }

        llm = BedrockLLM(model_id="amazon.nova-pro-v1:0")
        result = llm.invoke_with_tools("Check balance", tools=[])

        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "get_balance"
        assert result["tool_calls"][0]["args"] == {"user_id": "123"}
