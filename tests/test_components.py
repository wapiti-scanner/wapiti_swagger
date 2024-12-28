from wapiti_swagger.parser import extract_request_body, parse_components

components_data = {
    "schemas": {
        "BaseSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"}
            }
        },
        "DerivedSchema": {
            "$ref": "#/components/schemas/BaseSchema"
        }
    }
}

def test_parse_components():
    resolved = parse_components(components_data)

    # Assertions for resolved components
    assert "BaseSchema" in resolved["schemas"]
    assert "DerivedSchema" in resolved["schemas"]
    assert resolved["schemas"]["DerivedSchema"] == resolved["schemas"]["BaseSchema"]



reduced_swagger_with_custom_type = {
    "paths": {
        "/api/AmaApproval/report/userbehavior": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/AmaApprovalBehaviorInput"
                            }
                        },
                        "text/json": {
                            "schema": {
                                "$ref": "#/components/schemas/AmaApprovalBehaviorInput"
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "AmaApprovalBehaviorInput": {
                "type": "object",
                "properties": {
                    "behaviorType": {"$ref": "#/components/schemas/EnumAmaUserBehaviorType"},
                    "docFindingCategory": {"$ref": "#/components/schemas/EnumAmaDocFindingCategory"}
                }
            },
            "EnumAmaUserBehaviorType": {"type": "string", "enum": ["VIEWED", "EDITED"]},
            "EnumAmaDocFindingCategory": {"type": "string", "enum": ["FINDING1", "FINDING2"]}
        }
    }
}


def test_extract_request_body_with_custom_type():
    # Extract request body parameters
    request_body = reduced_swagger_with_custom_type["paths"]["/api/AmaApproval/report/userbehavior"]["post"]["requestBody"]
    parameters = extract_request_body(request_body)

    # Assertions for parameters
    assert len(parameters) == 2  # Two media types

    # Check first parameter
    param_json = parameters[0]
    assert param_json.media_type == "application/json"
    assert param_json.custom_type == "AmaApprovalBehaviorInput"

    # Check second parameter
    param_text_json = parameters[1]
    assert param_text_json.media_type == "text/json"
    assert param_text_json.custom_type == "AmaApprovalBehaviorInput"
