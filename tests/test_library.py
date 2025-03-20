from wapiti_swagger.models import Parameter, SwaggerRequest
from wapiti_swagger.parser import extract_parameter, extract_requests


def test_extract_parameter_with_inline_schema():
    param = {
        "name": "end",
        "in": "query",
        "schema": {
            "type": "string",
            "format": "date-time",
            "nullable": False
        }
    }

    extracted_param = extract_parameter(param)

    assert extracted_param.name == "end"
    assert extracted_param.location == "query"
    assert extracted_param.param_type == "string"
    assert extracted_param.param_format == "date-time"
    assert extracted_param.nullable is False
    assert extracted_param.default is None


def test_extract_enum_parameter():
    param = {
        "name": "status",
        "in": "query",
        "description": "Status values that need to be considered for filter",
        "required": True,
        "type": "array",
        "items": {
            "type": "string",
            "enum": [
                "available",
                "pending",
                "sold"
            ],
            "default": "available"
        },
        "collectionFormat": "multi"
    }

    extracted_param = extract_parameter(param)
    assert extracted_param.default == "available"


def test_extract_default_int_parameter():
    data = {
        "name": "ids",
        "in": "query",
        "required": False,
        "type": "array",
        "items": {
            "type": "integer",
            "default": 42
        }
    }
    parameter = extract_parameter(data)
    assert parameter.default == 42


def test_extract_default_int_parameter_openapi3():
    data = {
        "name": "ids",
        "in": "query",
        "required": False,
        "schema": {
            "type": "array",
            "items": {
                "type": "integer",
                "default": 42
            }
        }
    }
    parameter = extract_parameter(data)
    assert parameter.default == 42


reduced_swagger_data = {
    "paths": {
        "/api/WechatCall/GetSignature": {
            "post": {
                "tags": ["WechatCall"],
                "summary": "Get signature for WeChat API calls",
                "parameters": [
                    {
                        "name": "appId",
                        "in": "query",
                        "description": "The application ID",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "timestamp",
                        "in": "query",
                        "description": "The timestamp",
                        "schema": {
                            "$ref": "#/components/schemas/Timestamp"
                        }
                    }
                ]
            }
        }
    },
    "components": {
        "schemas": {
            "Timestamp": {
                "type": "string",
                "format": "date-time",
                "nullable": False
            }
        }
    }
}


def test_extract_requests():
    # Call extract_requests with the reduced Swagger data
    extracted_requests = extract_requests(reduced_swagger_data)

    # Assertions for the extracted request
    assert len(extracted_requests) == 1  # Only one request should be extracted
    request = extracted_requests[0]
    assert isinstance(request, SwaggerRequest)
    assert request.path == "/api/WechatCall/GetSignature"
    assert request.method == "POST"
    assert request.summary == "Get signature for WeChat API calls"
    assert len(request.parameters) == 2  # Two parameters should be extracted

    # Assertions for the first parameter (appId)
    param_app_id = request.parameters[0]
    assert isinstance(param_app_id, Parameter)
    assert param_app_id.name == "appId"
    assert param_app_id.location == "query"
    assert param_app_id.description == "The application ID"
    assert param_app_id.required is True
    assert param_app_id.param_type == "string"
    assert param_app_id.param_format == ""
    assert param_app_id.nullable is False

    # Assertions for the second parameter (timestamp)
    param_timestamp = request.parameters[1]
    assert isinstance(param_timestamp, Parameter)
    assert param_timestamp.name == "timestamp"
    assert param_timestamp.location == "query"
    assert param_timestamp.description == "The timestamp"
    assert param_timestamp.required is False
    assert param_timestamp.param_type == ""
    assert param_timestamp.custom_type == "Timestamp"
    assert param_timestamp.param_format == ""
    assert param_timestamp.nullable is False


def test_extract_path_level_parameters():
    data = {
        "paths": {
            "/v1.0/{accountId}/flavors": {
                "parameters": [
                    {
                        "name": "accountId",
                        "required": True,
                        "in": "path",
                        "type": "string",
                        "description": "The account ID of the owner of the specified instance.\n"
                    },
                    {
                        "name": "belongsTo",
                        "required": False,
                        "in": "query",
                        "type": "string",
                        "description": "Test.\n"
                    }
                ],
                "get": {
                    "operationId": "getFlavors",
                    "summary": "List flavors",
                    "description": "Lists information for all available flavors.\n",
                    "produces": [
                        "application/json"
                    ],
                    "responses": {
                        "200": {
                            "description": "200 response"
                        }
                    }
                }
            },
        }
    }

    extracted_requests = extract_requests(data)
    assert len(extracted_requests) == 1
    assert {param.name for param in extracted_requests[0].parameters} == {"accountId", "belongsTo"}
