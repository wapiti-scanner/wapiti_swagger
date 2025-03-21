import pytest

from wapiti_swagger.parser import generate_request_body_from_schema, parse

# Save the complex Swagger file content as a string
COMPLEX_SWAGGER = """
{
  "openapi": "3.0.0",
  "info": {
    "title": "Complex API Example",
    "version": "1.0.0"
  },
  "paths": {
    "/api/ComplexObject": {
      "post": {
        "summary": "Create a Complex Object",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ComplexObject"
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ComplexObject": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "format": "int64"
          },
          "name": {
            "type": "string"
          },
          "tags": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "children": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/ChildObject"
            }
          }
        },
        "required": ["id", "name", "children"]
      },
      "ChildObject": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": ["TypeA", "TypeB", "TypeC"]
          },
          "details": {
            "$ref": "#/components/schemas/DetailObject"
          }
        },
        "required": ["type"]
      },
      "DetailObject": {
        "type": "object",
        "properties": {
          "description": {
            "type": "string"
          },
          "value": {
            "type": "number",
            "format": "double"
          }
        },
        "required": ["description"]
      }
    }
  }
}
"""

@pytest.fixture(name="complex_swagger")
def complex_swagger_file(tmp_path):
    swagger_path = tmp_path / "complex_swagger.json"
    swagger_path.write_text(COMPLEX_SWAGGER)
    return swagger_path

def test_generate_request_body_with_complex_object(complex_swagger):
    # Parse the Swagger file
    parsed = parse(str(complex_swagger))

    # Find the POST request for /api/ComplexObject
    request = next(req for req in parsed.requests if req.path == "/api/ComplexObject" and req.method == "POST")

    # Generate the request body for the ComplexObject schema
    request_body = generate_request_body_from_schema(
        schema=request.parameters[0].schema,
        resolved_components=parsed.components
    )

    # Expected output
    expected_body = {
        "id": 1,
        "name": "default",
        "tags": ["default"],
        "children": [
            {
                "type": "TypeA",
                "details": {
                    "description": "default",
                    "value": 1.0
                }
            }
        ]
    }

    # Validate the generated request body
    assert request_body == expected_body



# Save the Swagger file as a string
HIERARCHY_SWAGGER = """
{
  "openapi": "3.0.0",
  "info": {
    "title": "Hierarchy API Example",
    "version": "1.0.0"
  },
  "paths": {
    "/api/ParentObject": {
      "post": {
        "summary": "Create a Parent Object",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ParentObject"
              }
            }
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "ParentObject": {
        "type": "object",
        "properties": {
          "parentId": {
            "type": "integer",
            "format": "int64"
          },
          "parentName": {
            "type": "string"
          },
          "children": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/ChildObject"
            }
          }
        },
        "required": ["parentId", "parentName"]
      },
      "ChildObject": {
        "type": "object",
        "properties": {
          "childId": {
            "type": "integer",
            "format": "int64"
          },
          "childName": {
            "type": "string"
          },
          "grandchildren": {
            "type": "array",
            "items": {
              "$ref": "#/components/schemas/GrandchildObject"
            }
          }
        },
        "required": ["childId", "childName"]
      },
      "GrandchildObject": {
        "type": "object",
        "properties": {
          "grandchildId": {
            "type": "integer",
            "format": "int64"
          },
          "grandchildName": {
            "type": "string"
          }
        },
        "required": ["grandchildId", "grandchildName"]
      }
    }
  }
}
"""

@pytest.fixture(name="hierarchy_file")
def hierarchy_swagger_file(tmp_path):
    swagger_path = tmp_path / "hierarchy_swagger.json"
    swagger_path.write_text(HIERARCHY_SWAGGER)
    return swagger_path

def test_generate_request_body_with_hierarchy(hierarchy_file):
    # Parse the Swagger file
    parsed = parse(str(hierarchy_file))

    # Find the POST request for /api/ParentObject
    request = next(req for req in parsed.requests if req.path == "/api/ParentObject" and req.method == "POST")

    # Generate the request body for the ParentObject schema
    request_body = generate_request_body_from_schema(
        schema=request.parameters[0].schema,
        resolved_components=parsed.components
    )

    # Expected output
    expected_body = {
        "parentId": 1,
        "parentName": "default",
        "children": [
            {
                "childId": 1,
                "childName": "default",
                "grandchildren": [
                    {
                        "grandchildId": 1,
                        "grandchildName": "default"
                    }
                ]
            }
        ]
    }

    # Validate the generated request body
    assert request_body == expected_body


STRING_FORMAT_OPENAPI = """
{
    "openapi": "3.0.1",
    "servers": [
        {
            "url": "https://fake.openapi.fr/"
        }
    ],
    "paths": {
        "/v1/yolo": {
            "put": {
                "tags": [
                    "Alarms"
                ],
                "operationId": "Alarms_Update",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/AlarmPutModel"
                            }
                        }
                    }
                }
            }
        }
     },
    "components": {
        "schemas": {
            "AlarmPutModel": {
                "required": [
                    "alarmState"
                ],
                "type": "object",
                "properties": {
                    "confirmingDateTime": {
                        "type": "string",
                        "format": "date-time",
                        "nullable": true
                    }
                },
                "additionalProperties": false
            }
        }
    }
}
"""

@pytest.fixture(name="openapi_string_format")
def openapi_string_format_file(tmp_path):
    swagger_path = tmp_path / "openapi_string_format.json"
    swagger_path.write_text(STRING_FORMAT_OPENAPI)
    return swagger_path

def test_generate_request_body_string_format(openapi_string_format):
    # Parse the Swagger file
    parsed = parse(str(openapi_string_format))

    # Find the POST request for /api/ParentObject
    request = parsed.requests[0]

    # Generate the request body for the ParentObject schema
    request_body = generate_request_body_from_schema(
        schema=request.parameters[0].schema,
        resolved_components=parsed.components
    )

    # Validate the generated request body
    assert request_body == {'confirmingDateTime': '2023-03-03T20:35:34.32'}
