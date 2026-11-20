import pytest

from wapiti_swagger.models import Parameter
from wapiti_swagger.parser import extract_requests, parse

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


# Reusable parameters, as defined in the "Components Object Example" of the OpenAPI 3.0.3 specification
OPENAPI_3_SPEC = {
    "openapi": "3.0.3",
    "paths": {
        "/pets": {
            "parameters": [
                {"$ref": "#/components/parameters/skipParam"},
                {"$ref": "#/components/parameters/limitParam"},
            ],
            "get": {"summary": "List pets"},
            "post": {
                "summary": "Add a new pet",
                # The operation redefines one of the parameters of the path
                "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20}}],
                "requestBody": {"$ref": "#/components/requestBodies/PetBody"},
            },
        },
    },
    "components": {
        "schemas": {"Pet": {"type": "object", "properties": {"name": {"type": "string"}}}},
        "parameters": {
            "skipParam": {
                "name": "skip",
                "in": "query",
                "description": "number of items to skip",
                "required": True,
                "schema": {"type": "integer", "format": "int32"},
            },
            "limitParam": {
                "name": "limit",
                "in": "query",
                "description": "max records to return",
                "required": True,
                "schema": {"type": "integer", "format": "int32"},
            },
        },
        "requestBodies": {
            "PetBody": {
                "description": "A JSON object containing pet information",
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}},
            },
        },
    },
}

SKIP_PARAMETER = Parameter(
    name="skip",
    location="query",
    description="number of items to skip",
    required=True,
    param_type="integer",
    param_format="int32",
    schema={"type": "integer", "format": "int32"},
)


def test_openapi_3_reusable_parameters():
    list_pets = extract_requests(OPENAPI_3_SPEC)[0]

    assert list_pets.parameters == [
        SKIP_PARAMETER,
        Parameter(
            name="limit",
            location="query",
            description="max records to return",
            required=True,
            param_type="integer",
            param_format="int32",
            schema={"type": "integer", "format": "int32"},
        ),
    ]


def test_operation_parameters_override_path_parameters():
    add_pet = extract_requests(OPENAPI_3_SPEC)[1]

    # "limit" is the one of the operation, and it is not duplicated
    assert add_pet.parameters[:2] == [
        SKIP_PARAMETER,
        Parameter(
            name="limit",
            location="query",
            param_type="integer",
            default=20,
            schema={"type": "integer", "default": 20},
        ),
    ]


def test_openapi_3_reusable_request_body():
    add_pet = extract_requests(OPENAPI_3_SPEC)[1]

    assert add_pet.parameters[2:] == [
        Parameter(
            name="body",
            location="body",
            description="Request body for application/json",
            required=True,
            media_type="application/json",
            custom_type="Pet",
            schema={"$ref": "#/components/schemas/Pet"},
        )
    ]


def test_schema_reference_is_not_mistaken_for_a_parameter_reference():
    spec = {
        "swagger": "2.0",
        "paths": {
            "/pets": {
                "post": {
                    "parameters": [{"name": "body", "in": "body", "schema": {"$ref": "#/definitions/Pet"}}],
                },
            },
        },
        # A reusable parameter and a schema with the same name
        "parameters": {"Pet": {"name": "pet", "in": "query", "type": "string"}},
        "definitions": {"Pet": {"type": "object"}},
    }

    (parameter,) = extract_requests(spec)[0].parameters
    assert (parameter.name, parameter.location, parameter.custom_type) == ("body", "body", "Pet")


@pytest.mark.parametrize(
    "ref",
    [
        "#/components/parameters/missing",
        "#/components/parameters/skipParam/name",  # Not an object
        "parameters.yaml#/limitParam",  # Other file
        None,
    ],
)
def test_unresolvable_parameter_reference_is_kept_as_is(ref):
    spec = {**OPENAPI_3_SPEC, "paths": {"/pets": {"get": {"parameters": [{"$ref": ref}]}}}}

    (parameter,) = extract_requests(spec)[0].parameters
    assert parameter.name == ""
    assert parameter.schema == {"$ref": ref}


def test_reference_with_escaped_characters():
    # "~1" stands for "/" in a JSON pointer
    spec = {
        "openapi": "3.0.3",
        "paths": {
            "/pets": {"get": {"parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}]}},
            "/dogs": {
                "get": {
                    "parameters": [
                        {"$ref": "#/paths/~1pets/parameters/0"},  # Not an object: a list is not walked through
                        {"$ref": "#/paths/~1pets/get/parameters"},  # Not an object either
                        {"$ref": "#/components/parameters/a~0b"},
                    ]
                }
            },
        },
        "components": {"parameters": {"a~b": {"name": "tilde", "in": "query"}}},
    }

    parameters = extract_requests(spec)[1].parameters
    assert [parameter.name for parameter in parameters] == ["", "", "tilde"]
