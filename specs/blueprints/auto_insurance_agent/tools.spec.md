# Blueprint: Auto-Insurance Agent Tools

## Purpose
Defines the tools available to the `AutoInsuranceAgent` LLM for retrieving and updating mock policy data. To simulate a real-world architecture, tool functions will call a service layer (`auto_ins_service`) which in turn queries a mock database module (`mock_db.py`). 

## Implements Features
- F-007: Auto-Insurance Agent

## Data Models

### Mock Database (`agents/auto_insurance_agent/mock_db.py`)
This module will hold the in-memory state representing the persistent datastore. It supports multiple policies per member.

```python
MOCK_POLICIES = {
    "MEMBER-123": [
        {
            "policy_id": "AUTO-999888",
            "start_date": "2026-01-15",
            "expiry_date": "2027-01-15",
            "premium": 1250.00,
            "deductibles": {
                "comprehensive": 500.00,
                "liability": 0.00
            },
            "drivers": ["Alice Smith"]
        }
    ]
}
```

## Interface Contract

### `get_policy_details`
- **Input**: `member_id` (string)
- **Output**: JSON string of policy details (or an error message if not found).
- **Behavior**: Calls the `auto_ins_service` to fetch the list of policies for the given `member_id` from `mock_db.py`. For this phase, if multiple policies exist, returning the first/active one is sufficient for the demo.
- **Schema**:
```json
{
    "name": "get_policy_details",
    "description": "Retrieve the active auto insurance policy details for a given member.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "member_id": {
                    "type": "string",
                    "description": "The unique identifier of the member."
                }
            },
            "required": ["member_id"]
        }
    }
}
```

### `add_driver`
- **Input**: `member_id` (string), `driver_name` (string)
- **Output**: Success/Failure string message.
- **Behavior**: Calls the `auto_ins_service` to append `driver_name` to the policy's `drivers` list in `mock_db.py`. If `driver_name` is missing from the user's request, the LLM must prompt the user for the name before calling the tool.
- **Schema**:
```json
{
    "name": "add_driver",
    "description": "Add a new driver to the active auto insurance policy.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "member_id": {
                    "type": "string"
                },
                "driver_name": {
                    "type": "string",
                    "description": "The full name of the driver to be added."
                }
            },
            "required": ["member_id", "driver_name"]
        }
    }
}
```

### `remove_driver`
- **Input**: `member_id` (string), `driver_name` (string)
- **Output**: Success/Failure string message.
- **Behavior**: Calls the `auto_ins_service` to remove `driver_name` from the policy's `drivers` list. **Rejects** the removal if the `driver_name` is the only remaining driver on the policy. If `driver_name` is missing from the user's request, the LLM must prompt the user for the name before calling the tool.
- **Schema**:
```json
{
    "name": "remove_driver",
    "description": "Remove an existing driver from the active auto insurance policy.",
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "member_id": {
                    "type": "string"
                },
                "driver_name": {
                    "type": "string",
                    "description": "The full name of the driver to be removed."
                }
            },
            "required": ["member_id", "driver_name"]
        }
    }
}
```

## Acceptance Criteria
- [ ] `mock_db.py` is utilized to simulate remote API/database calls.
- [ ] `get_policy_details` accurately returns a policy containing `start_date`, `expiry_date`, `premium`, `deductibles` (comprehensive/liability), and `drivers`.
- [ ] `add_driver` and `remove_driver` require both `member_id` and `driver_name`.
- [ ] `remove_driver` strictly prevents the removal of the only driver on a policy.

## Dependencies
- Internal mock service/database (`agents.auto_insurance_agent.mock_db` and `agents.auto_insurance_agent.service`)
