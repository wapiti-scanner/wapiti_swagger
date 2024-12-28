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

@pytest.fixture
def complex_swagger_file(tmp_path):
    swagger_path = tmp_path / "complex_swagger.json"
    swagger_path.write_text(COMPLEX_SWAGGER)
    return swagger_path

def test_generate_request_body_with_complex_object(complex_swagger_file):
    # Parse the Swagger file
    parsed = parse(str(complex_swagger_file))

    # Find the POST request for /api/ComplexObject
    request = next(req for req in parsed.requests if req.path == "/api/ComplexObject" and req.method == "POST")

    # Generate the request body for the ComplexObject schema
    request_body = generate_request_body_from_schema(
        schema=request.parameters[0].schema,
        resolved_components=parsed.components
    )

    # Expected output
    expected_body = {
        "id": 0,
        "name": "example",
        "tags": ["example"],
        "children": [
            {
                "type": "TypeA",
                "details": {
                    "description": "example",
                    "value": 0.0
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

@pytest.fixture
def hierarchy_swagger_file(tmp_path):
    swagger_path = tmp_path / "hierarchy_swagger.json"
    swagger_path.write_text(HIERARCHY_SWAGGER)
    return swagger_path

def test_generate_request_body_with_hierarchy(hierarchy_swagger_file):
    # Parse the Swagger file
    parsed = parse(str(hierarchy_swagger_file))

    # Find the POST request for /api/ParentObject
    request = next(req for req in parsed.requests if req.path == "/api/ParentObject" and req.method == "POST")

    # Generate the request body for the ParentObject schema
    request_body = generate_request_body_from_schema(
        schema=request.parameters[0].schema,
        resolved_components=parsed.components
    )

    # Expected output
    expected_body = {
        "parentId": 0,
        "parentName": "example",
        "children": [
            {
                "childId": 0,
                "childName": "example",
                "grandchildren": [
                    {
                        "grandchildId": 0,
                        "grandchildName": "example"
                    }
                ]
            }
        ]
    }

    # Validate the generated request body
    assert request_body == expected_body
