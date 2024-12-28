from wapiti_swagger.models import SwaggerRequest
from wapiti_swagger.parser import extract_request_body, extract_requests

swagger_data_with_body = {
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
                    }
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/SignatureRequest"
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "SignatureRequest": {
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "nonce": {
                        "type": "string"
                    }
                },
                "required": ["timestamp"]
            }
        }
    }
}

def test_extract_requests_with_request_body():
    # Call extract_requests with the reduced Swagger data
    extracted_requests = extract_requests(swagger_data_with_body)

    # Assertions for the extracted request
    assert len(extracted_requests) == 1
    request = extracted_requests[0]
    assert isinstance(request, SwaggerRequest)
    assert request.path == "/api/WechatCall/GetSignature"
    assert request.method == "POST"
    assert request.summary == "Get signature for WeChat API calls"

    # Check parameters
    assert len(request.parameters) == 2  # One query param + one body params

    # Query parameter: appId
    param_app_id = request.parameters[0]
    assert param_app_id.name == "appId"
    assert param_app_id.location == "query"
    assert param_app_id.param_type == "string"
    assert param_app_id.custom_type is None

    # Body parameter: timestamp
    param_timestamp = request.parameters[1]
    assert param_timestamp.name == "body"
    assert param_timestamp.location == "body"
    assert param_timestamp.param_type == ""
    assert param_timestamp.custom_type == "SignatureRequest"
    assert param_timestamp.description == "Request body for application/json"


swagger_with_multiple_content_types = {
    "paths": {
        "/api/WechatCall/GetSignature": {
            "post": {
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/SignatureRequest"
                            }
                        },
                        "application/xml": {
                            "schema": {
                                "$ref": "#/components/schemas/SignatureRequest"
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "SignatureRequest": {
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "nonce": {
                        "type": "string"
                    }
                },
                "required": ["timestamp"]
            }
        }
    }
}


def test_extract_request_body_with_media_type():
    # Call extract_request_body with reduced Swagger data
    request_body = swagger_with_multiple_content_types["paths"]["/api/WechatCall/GetSignature"]["post"]["requestBody"]

    parameters = extract_request_body(request_body)

    # Assertions for parameters
    assert len(parameters) == 2  # One parameter per content type

    # Check application/json parameter
    param_json = parameters[0]
    assert param_json.name == "body"
    assert param_json.media_type == "application/json"
    assert param_json.description == "Request body for application/json"
    assert param_json.param_type == ""
    assert param_json.custom_type == "SignatureRequest"

    # Check application/xml parameter
    param_xml = parameters[1]
    assert param_xml.name == "body"
    assert param_xml.media_type == "application/xml"
    assert param_xml.description == "Request body for application/xml"
    assert param_xml.param_type == ""
    assert param_xml.custom_type == "SignatureRequest"
