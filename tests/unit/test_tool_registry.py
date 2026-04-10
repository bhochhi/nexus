from nexus.tools.banking import register_banking_tools
from nexus.tools.faq import register_faq_tools
from nexus.tools.insurance import register_insurance_tools
from nexus.tools.registry import ToolRegistry


def test_register_and_get_tool():
    registry = ToolRegistry()
    register_banking_tools(registry)

    tool = registry.get("get_account_balance")
    assert tool.name == "get_account_balance"


def test_list_tools():
    registry = ToolRegistry()
    register_banking_tools(registry)
    register_insurance_tools(registry)
    register_faq_tools(registry)

    tools = registry.list_tools()
    names = [t["name"] for t in tools]

    assert "get_account_balance" in names
    assert "file_claim" in names
    assert "answer_faq" in names
    assert len(tools) == 10  # 5 banking + 4 insurance + 1 faq


def test_tool_execution():
    registry = ToolRegistry()
    register_banking_tools(registry)

    tool = registry.get("get_account_balance")
    result = tool.execute({"user_id": "test-user", "account_type": "checking"})

    assert result["status"] == "success"
    assert result["balance"] == 4250.75


def test_get_unknown_tool_raises():
    registry = ToolRegistry()
    try:
        registry.get("nonexistent")
        assert False, "Should have raised KeyError"
    except KeyError:
        pass
