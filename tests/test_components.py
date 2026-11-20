import json
import os
from tempfile import NamedTemporaryFile

from wapiti_swagger.parser import extract_request_body, parse, parse_components, resolve_schema

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
    request_body = reduced_swagger_with_custom_type["paths"]["/api/AmaApproval/report/userbehavior"]["post"][
        "requestBody"]
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
        'parameters': {},
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


openapi_2_definitions_missing_type = {
    "paths": {
        "/ftpusers/{name}": {
            "put": {
                "tags": [
                    "FtpUsers"
                ],
                "summary": "Update FTP user",
                "consumes": [
                    "application/json"
                ],
                "produces": [
                    "application/json"
                ],
                "parameters": [
                    {
                        "in": "path",
                        "name": "name",
                        "description": "FTP user name",
                        "required": True,
                        "type": "string",
                        "x-example": "exampleuser"
                    },
                    {
                        "in": "body",
                        "name": "body",
                        "description": "FTP User data",
                        "required": True,
                        "schema": {
                            "$ref": "#/definitions/FtpUserUpdateRequest"
                        }
                    }
                ]
            }
        },
    },
    "definitions": {
        "FtpUserUpdateRequest": {
            # Object has properties but type "object" is not explicit
            "properties": {
                "name": {
                    "description": "User name in the system",
                    "type": "string",
                    "example": "exampleuser"
                },
                "password": {
                    "description": "User password",
                    "type": "string"
                },
            }
        },
    }
}


def test_swagger_2_0_definitions_missing_type():
    with NamedTemporaryFile("w", suffix=".json", delete=False) as file_obj:
        json.dump(openapi_2_definitions_missing_type, file_obj)
        filename = file_obj.name

    parsed_swagger = parse(file_obj.name)
    assert parsed_swagger.components == {
        'parameters': {},
        'schemas': {
            "FtpUserUpdateRequest": {
                # Object has properties but type "object" is not explicit
                "properties": {
                    "name": {
                        "description": "User name in the system",
                        "type": "string",
                        "example": "exampleuser"
                    },
                    "password": {
                        "description": "User password",
                        "type": "string"
                    },
                }
            },
        }
    }
    os.unlink(filename)


def test_parse_components_breaks_circular_references():
    components = {
        "schemas": {
            "Node": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "parent": {"$ref": "#/components/schemas/Node"},
                },
            }
        }
    }

    resolved = parse_components(components)
    node = resolved["schemas"]["Node"]
    # The first level of self-reference is inlined, the next one is dropped
    assert node["properties"]["parent"] == {"type": "object", "properties": {"name": {"type": "string"}}}


def test_parse_components_reuses_cached_references():
    components = {
        "schemas": {
            "Address": {"type": "object", "properties": {"city": {"type": "string"}}},
            "Order": {
                "type": "object",
                "properties": {
                    "billing": {"$ref": "#/components/schemas/Address"},
                    "shipping": {"$ref": "#/components/schemas/Address"},
                },
            },
        }
    }

    resolved = parse_components(components)
    properties = resolved["schemas"]["Order"]["properties"]
    assert properties["billing"] == properties["shipping"] == components["schemas"]["Address"]
    # Cached results are copied, so each property can be modified independently
    assert properties["billing"] is not properties["shipping"]


def test_parse_components_drops_unresolvable_references():
    components = {"schemas": {"Alias": {"$ref": "#/components/schemas/Missing"}}}
    assert parse_components(components) == {"schemas": {}, "parameters": {}}


def test_parse_components_ignores_sections_which_are_not_dictionaries():
    components = {"schemas": {"Pet": {"type": "string"}}, "x-internal": True}
    assert parse_components(components) == {"schemas": {"Pet": {"type": "string"}}, "parameters": {}}


def test_parse_components_without_schemas_section():
    # References can't be resolved, but this must not be fatal
    components = {"parameters": {"limit": {"$ref": "#/components/schemas/Missing"}, "offset": {"name": "offset"}}}
    assert parse_components(components) == {"schemas": {}, "parameters": {"offset": {"name": "offset"}}}


def test_resolve_schema():
    components = {"schemas": {"Tag": {"type": "string"}}}
    schema = {"type": "array", "items": {"$ref": "#/components/schemas/Tag"}}

    assert resolve_schema(schema, components) == {"type": "array", "items": {"type": "string"}}
    assert resolve_schema({"$ref": "#/components/schemas/Missing"}, components) is None
    # Without components, nothing can be resolved: array items are left untouched
    assert resolve_schema(schema, {}) == schema
