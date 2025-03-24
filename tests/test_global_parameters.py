import pytest

from wapiti_swagger.models import Parameter
from wapiti_swagger.parser import parse

# Save the complex Swagger file content as a string
COMPLEX_SWAGGER = """
{
    "swagger": "2.0",
    "info": {
        "title": "Complexe Swagger",
        "description": "API",
        "version": "2.0"
    },
    "host": "fakeSwagger.fr",
    "schemes": [
        "http",
        "https"
    ],
    "basePath": "/api/v2.0",
    "produces": [
        "application/json"
    ],
    "consumes": [
        "application/json"
    ],
    "paths": {
        "/projects/{project_name_or_id}": {
            "get": {
                "summary": "Return specific project detail information",
                "description": "This endpoint returns specific project information by project ID.",
                "tags": [
                    "project"
                ],
                "operationId": "getProject",
                "parameters": [
                    {
                        "$ref": "#/parameters/requestId"
                    },
                    {
                        "$ref": "#/parameters/isResourceName"
                    },
                    {
                        "$ref": "#/parameters/projectNameOrId"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Return matched project information.",
                        "schema": {
                            "$ref": "#/definitions/Project"
                        }
                    },
                    "401": {
                        "$ref": "#/responses/401"
                    },
                    "500": {
                        "$ref": "#/responses/500"
                    }
                }
            }
        }
    },
    "parameters": {
        "requestId": {
            "name": "X-Request-Id",
            "description": "An unique ID for the request",
            "in": "header",
            "type": "string",
            "required": false,
            "minLength": 1
        },
        "isResourceName": {
            "name": "X-Is-Resource-Name",
            "description": "The flag to indicate etc.",
            "in": "header",
            "type": "boolean",
            "required": false,
            "default": false
        },
        "projectNameOrId": {
            "name": "project_name_or_id",
            "in": "path",
            "description": "The name or id of the project",
            "required": true,
            "type": "string"
        }
    }
}
"""


@pytest.fixture(name="global_parameters")
def complex_swagger_file(tmp_path):
    swagger_path = tmp_path / "complex_swagger.json"
    swagger_path.write_text(COMPLEX_SWAGGER)
    return swagger_path


def test_extract_and_use_global_parameters(global_parameters):
    # Parse the Swagger file
    parsed = parse(str(global_parameters))

    request = parsed.requests[0]

    assert request.parameters == [
        Parameter(
            name="X-Request-Id",
            location="header",
            param_type="string",
            description="An unique ID for the request",
            schema={
                "description": "An unique ID for the request",
                "in": "header",
                "minLength": 1,
                "name": "X-Request-Id",
                "required": False,
                "type": "string",
            },
        ),

        Parameter(
            name="X-Is-Resource-Name",
            location="header",
            param_type="boolean",
            default=False,
            description="The flag to indicate etc.",
            schema={
                "default": False,
                "description": "The flag to indicate etc.",
                "in": "header",
                "name": "X-Is-Resource-Name",
                "required": False,
                "type": "boolean"
            },
        ),

        Parameter(
            name="project_name_or_id",
            location="path",
            param_type="string",
            required=True,
            description="The name or id of the project",
            schema={
                "description": "The name or id of the project",
                "in": "path",
                "name": "project_name_or_id",
                "required": True,
                "type": "string",
            }
        ),
    ]
