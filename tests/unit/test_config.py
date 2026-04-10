from nexus.config import Settings


def test_default_settings():
    s = Settings(
        aws_region="us-east-1",
        bedrock_model_id="amazon.nova-pro-v1:0",
        llm_provider="bedrock",
    )
    assert s.aws_region == "us-east-1"
    assert s.bedrock_model_id == "amazon.nova-pro-v1:0"
    assert s.llm_provider == "bedrock"
    assert s.session_store_type == "memory"
