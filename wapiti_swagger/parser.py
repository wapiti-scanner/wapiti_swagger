"""This module turns a Swagger (openAPI) file into the list of HTTP requests accepted by the API"""

import json
from typing import Any, Dict, List

import yaml

# Imported here so that everything can be found in `wapiti_swagger.parser`
from wapiti_swagger.components import find_referenced_object, parse_components, ref_name, resolve_schema
from wapiti_swagger.examples import RequestBody, default_string_values, generate_request_body_from_schema
from wapiti_swagger.models import Parameter, ParsedSwagger, SwaggerRequest

__all__ = [
    "RequestBody",
    "default_string_values",
    "extract_metadata",
    "extract_parameter",
    "extract_request_body",
    "extract_requests",
    "generate_request_body_from_schema",
    "parse",
    "parse_components",
    "resolve_schema",
]

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


def parse(file_path: str) -> ParsedSwagger:
    """
    Parses a Swagger or OpenAPI file (JSON or YAML) and returns the extracted requests and components.

    :param file_path: Path to the Swagger/OpenAPI file.
    :return: A ParsedSwagger object with extracted requests and resolved components.
    """
    data = load_file(file_path)
    if "paths" not in data:
        raise ValueError("Invalid Swagger/OpenAPI file: Missing 'paths' key.")

    return ParsedSwagger(
        metadata=extract_metadata(data),
        requests=extract_requests(data),
        components=extract_components(data),
    )


def load_file(file_path: str) -> dict:
    """Reads a JSON or YAML file, the format is deduced from the file extension."""
    with open(file_path, "r", encoding="utf-8") as f:
        if file_path.endswith(".json"):
            return json.load(f)
        if file_path.endswith((".yaml", ".yml")):
            return yaml.safe_load(f)
        raise ValueError("Unsupported file format. Use JSON or YAML.")


def extract_components(data: dict) -> Dict[str, Dict[str, dict]]:
    """
    Extracts the reusable schemas and parameters of the Swagger file, with their `$ref` entries resolved.

    :param data: The Swagger/OpenAPI specification as a dictionary.
    :return: The resolved components, or an empty dictionary if the file doesn't define any.
    """
    # OpenAPI 3.x
    if "components" in data:
        return parse_components(data["components"])

    # Swagger 2.0: same content, at the root of the file under different names
    if "definitions" in data or "parameters" in data:
        return parse_components(
            {
                "schemas": data.get("definitions", {}),
                "parameters": data.get("parameters", {}),
            }
        )

    return {}


def extract_metadata(data: dict) -> Dict[str, Any]:
    """
    Extracts metadata from the root of the Swagger file.

    :param data: The Swagger/OpenAPI specification as a dictionary.
    :return: A dictionary containing metadata such as host, basePath, schemes, servers, etc.
    """
    metadata = {
        # Swagger 2.0
        "host": data.get("host"),
        "basePath": data.get("basePath"),
        "schemes": data.get("schemes"),
        # OpenAPI 3.x
        "servers": [
            get_server_url(server) for server in data.get("servers", []) if isinstance(server, dict) and "url" in server
        ],
    }
    return {key: value for key, value in metadata.items() if value is not None}


def get_server_url(server: dict) -> str:
    """
    Returns the URL of a server, with its variables replaced by their default value.

    Example: "https://{region}.example.com" gives "https://eu.example.com" if `region` defaults to "eu".
    """
    url = server["url"]
    for variable_name, properties in server.get("variables", {}).items():
        if "default" in properties:
            url = url.replace(f"{{{variable_name}}}", properties["default"])
    return url


def extract_requests(data: dict) -> List[SwaggerRequest]:
    """
    Extracts the HTTP requests from the `paths` section of the Swagger specification.

    :param data: The Swagger/OpenAPI specification as a dictionary.
    :return: One SwaggerRequest per path and HTTP method.
    """
    if "paths" not in data:
        raise ValueError("Invalid Swagger file: 'paths' section is missing.")

    requests = []
    for path, path_item in data["paths"].items():
        # Along with its methods, a path can hold parameters which apply to all of them
        path_parameters = extract_parameters(path_item, data)

        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue

            parameters = merge_parameters(path_parameters, extract_parameters(operation, data))
            if "requestBody" in operation:
                parameters += extract_request_body(follow_reference(operation["requestBody"], data))

            requests.append(
                SwaggerRequest(
                    path=path,
                    method=method.upper(),
                    summary=operation.get("summary", ""),
                    parameters=parameters,
                    consumes=operation.get("consumes", []),
                )
            )
    return requests


def follow_reference(item: dict, data: dict) -> dict:
    """
    Returns the reusable definition a parameter or a request body points to.

    Instead of being described in place, a parameter or a request body can be a reference to a definition
    shared by several operations: {"$ref": "#/parameters/limitParam"} in Swagger 2.0,
    {"$ref": "#/components/parameters/limitParam"} or {"$ref": "#/components/requestBodies/PetBody"} in OpenAPI 3.x.

    :param item: A parameter or request body dictionary.
    :param data: The Swagger/OpenAPI specification as a dictionary.
    :return: The definition, or the item itself if it is not a reference or if the definition can't be found.
    """
    if "$ref" not in item:
        return item
    return find_referenced_object(data, item["$ref"]) or item


def extract_parameters(section: dict, data: dict) -> List[Parameter]:
    """
    Extracts the `parameters` list of a path or of an operation.

    :param section: The path or operation dictionary.
    :param data: The Swagger/OpenAPI specification as a dictionary, where reusable parameters are looked up.
    """
    return [extract_parameter(follow_reference(param, data)) for param in section.get("parameters", [])]


def merge_parameters(path_parameters: List[Parameter], operation_parameters: List[Parameter]) -> List[Parameter]:
    """
    Returns the parameters of an operation: the ones of its path, then its own.

    A parameter of the operation overrides the parameter of the path having the same name and location.
    """
    overridden = {(parameter.name, parameter.location) for parameter in operation_parameters}
    inherited = [parameter for parameter in path_parameters if (parameter.name, parameter.location) not in overridden]
    return inherited + operation_parameters


def extract_parameter(param: dict) -> Parameter:
    """
    Extracts a Parameter object from a parameter dictionary.

    :param param: Dictionary representing a parameter.
    :return: Parameter object with raw schema.
    """
    # OpenAPI 3.x describes the value in a "schema" entry, Swagger 2.0 directly in the parameter
    # (except for body parameters).
    schema = param.get("schema", param)

    return Parameter(
        name=param.get("name", ""),
        description=param.get("description", ""),
        location=param.get("in", ""),
        required=param.get("required", False),
        param_type=schema.get("type", ""),
        param_format=schema.get("format", ""),
        nullable=schema.get("nullable", False),
        default=get_default_value(param, schema),
        custom_type=ref_name(schema),
        schema=schema,
    )


def get_default_value(param: dict, schema: dict) -> Any:
    """Returns the default value of a parameter, or None if it doesn't have any."""
    default = schema.get("default", param.get("default"))

    if schema.get("type") == "array" and "items" in schema:
        # An array gets the default value of its items, or else the first value they accept
        items = schema["items"]
        accepted_values = items.get("enum") or [None]
        default = items.get("default", default) or accepted_values[0]

    return default


def extract_request_body(request_body: dict) -> List[Parameter]:
    """
    Extracts parameters from a requestBody definition (OpenAPI 3.x).

    :param request_body: Dictionary representing the requestBody.
    :return: One "body" Parameter per media type accepted by the operation.
    """
    parameters = []
    for media_type, media_details in request_body.get("content", {}).items():
        schema = media_details.get("schema", {})
        parameters.append(
            Parameter(
                name="body",
                description=f"Request body for {media_type}",
                location="body",
                required=request_body.get("required", False),
                param_type=schema.get("type", ""),
                param_format=schema.get("format", ""),
                nullable=schema.get("nullable", False),
                media_type=media_type,
                custom_type=ref_name(schema),
                schema=schema,
            )
        )
    return parameters
