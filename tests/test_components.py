import json
import os
from tempfile import NamedTemporaryFile

from wapiti_swagger.parser import extract_request_body, parse_components, parse

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


openapi_2_definitions_dict = {
    "paths": {
        "/pet/{petId}/uploadImage": {
            "post": {
                "tags": [
                    "pet"
                ],
                "summary": "uploads an image",
                "description": "",
                "operationId": "uploadFile",
                "consumes": [
                    "multipart/form-data"
                ],
                "produces": [
                    "application/json"
                ],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "description": "ID of pet to update",
                        "required": True,
                        "type": "integer",
                        "format": "int64"
                    },
                    {
                        "name": "additionalMetadata",
                        "in": "formData",
                        "description": "Additional data to pass to server",
                        "required": False,
                        "type": "string"
                    },
                    {
                        "name": "file",
                        "in": "formData",
                        "description": "file to upload",
                        "required": False,
                        "type": "file"
                    }
                ],
            }
        }
    },
    "definitions": {
        "ApiResponse": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "integer",
                    "format": "int32"
                },
                "type": {
                    "type": "string"
                },
                "message": {
                    "type": "string"
                }
            }
        }
    }
}

def test_swagger_2_0_definitions():
    with NamedTemporaryFile("w", suffix=".json", delete=False) as file_obj:
        json.dump(openapi_2_definitions_dict, file_obj)
        filename = file_obj.name

    parsed_swagger = parse(file_obj.name)
    assert parsed_swagger.components == {
        'schemas': {
            'ApiResponse': {
                'type': 'object',
                'properties': {
                    'code': {
                        'type': 'integer',
                        'format': 'int32'
                    },
                    'type': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        }
    }
    os.unlink(filename)













