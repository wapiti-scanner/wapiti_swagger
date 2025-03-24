"""This module contains functions to parse several sections of a swagger (openAPI) file"""
import json
import logging
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import yaml

from wapiti_swagger.models import Parameter, ParsedSwagger, SwaggerRequest


# Define a custom type alias for request body generation
RequestBody = Union[Dict[str, Any], List[Any], str, int, float, bool]


def parse(file_path: str) -> ParsedSwagger:
    """
    Parses a Swagger or OpenAPI file (JSON or YAML) and returns the extracted requests and components.

    :param file_path: Path to the Swagger/OpenAPI file.
    :return: A ParsedSwagger object with extracted requests and resolved components.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.endswith('.json'):
            data = json.load(f)
        elif file_path.endswith(('.yaml', '.yml')):
            data = yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format. Use JSON or YAML.")

    if "paths" not in data:
        raise ValueError("Invalid Swagger/OpenAPI file: Missing 'paths' key.")

    metadata = extract_metadata(data)
    requests = extract_requests(data)

    # Handle both OpenAPI 3.x and Swagger 2.0
    components = {}
    if "components" in data:
        components = parse_components(data["components"])
    elif "definitions" in data or "parameters" in data:
        components = parse_components(
            {
                "schemas": data.get("definitions", {}),
                "parameters": data.get("parameters", {})
            }
        )

    return ParsedSwagger(metadata=metadata, requests=requests, components=components)


def extract_metadata(data: dict) -> Dict[str, Any]:
    """
    Extracts metadata from the root of the Swagger file.

    :param data: The Swagger/OpenAPI specification as a dictionary.
    :return: A dictionary containing metadata such as host, basePath, schemes, servers, etc.
    """
    metadata = {
        "host": data.get("host"),
        "basePath": data.get("basePath"),
        "schemes": data.get("schemes"),
        "servers": [],
    }

    # OpenAPI 3.x
    for server in data.get("servers", []):
        if isinstance(server, dict) and "url" in server:
            url = server["url"]
            for variable_name, properties in server.get("variables", {}).items():
                if "default" in properties:
                    url = url.replace(
                        f"{{{variable_name}}}", properties["default"]
                    )

            metadata["servers"].append(url)

    # Remove None values
    return {key: value for key, value in metadata.items() if value is not None}


def replace_with_global_parameters(parameters: List[Parameter], global_params: Dict[str, Parameter]) -> List[Parameter]:
    """Replace parameters in list with their real version from the global parameters list when possible."""
    return [global_params[param.custom_type] if param.custom_type in global_params else param for param in parameters]

def extract_requests(data: dict):
    """Extracts HTTP requests from the Swagger specification."""
    if "paths" not in data:
        raise ValueError("Invalid Swagger file: 'paths' section is missing.")

    requests = []
    global_parameters = {name: extract_parameter(value) for name, value in data.get("parameters", {}).items()}

    for path, methods in data["paths"].items():
        # Some parameters in common for all methods may be put at the same level that generic methods
        path_level_parameters = [extract_parameter(param) for param in methods.get("parameters", [])]
        for method, details in methods.items():
            if method.lower() in {"get", "post", "put", "delete", "patch", "options", "head"}:
                method_level_parameters = [extract_parameter(param) for param in details.get("parameters", [])]

                # Handle requestBody
                if "requestBody" in details:
                    request_body_params = extract_request_body(details["requestBody"])
                    method_level_parameters.extend(request_body_params)

                # Extract consumes
                consumes = details.get("consumes", [])

                fixed_parameters = replace_with_global_parameters(
                    path_level_parameters + method_level_parameters,
                    global_parameters,
                )

                requests.append(SwaggerRequest(
                    path=path,
                    method=method.upper(),
                    summary=details.get("summary", ""),
                    parameters=fixed_parameters,
                    consumes=consumes,
                ))
    return requests


# pylint: disable=too-many-return-statements
def resolve_schema(
        schema: dict, resolved_components: dict, visited_refs: set = None, resolved_cache: dict = None
) -> Optional[dict]:
    """
    Recursively resolves $ref entries within a schema, avoiding circular references in the object graph.

    :param schema: The schema to resolve.
    :param resolved_components: The resolved components dictionary.
    :param visited_refs: Tracks visited $refs to prevent infinite recursion.
    :param resolved_cache: Caches already resolved schemas to prevent redundant work.
    :return: The fully resolved schema, or None if a circular reference is detected.
    """
    if visited_refs is None:
        visited_refs = set()
    if resolved_cache is None:
        resolved_cache = {}

    # If the schema is empty, return as-is
    if not schema:
        return schema

    # Handle $ref resolution
    if "$ref" in schema:
        ref = schema["$ref"]

        if ref in resolved_cache:
            # If already resolved, return a deep copy of the cached result
            return resolved_cache[ref].copy() if resolved_cache[ref] else None

        if ref in visited_refs:
            # Log and break the circular reference
            logging.debug("Breaking circular reference: %s", ref)
            resolved_cache[ref] = None  # Mark as skipped
            return None

        # Mark as in-progress in the cache to prevent recursion
        resolved_cache[ref] = None

        # Add the current $ref to the visited set
        visited_refs.add(ref)

        # Resolve the referenced schema
        ref_name = ref.split("/")[-1]
        referenced_schema = resolved_components["schemas"].get(ref_name, {})
        resolved = resolve_schema(referenced_schema, resolved_components, visited_refs, resolved_cache)

        # Remove the current $ref from the visited set after resolution
        visited_refs.remove(ref)

        # Update the cache with the resolved schema
        resolved_cache[ref] = resolved.copy() if resolved else None
        return resolved.copy() if resolved else None

    # Handle object schemas with properties
    if schema.get("type") == "object" and "properties" in schema:
        schema_copy = schema.copy()
        schema_copy["properties"] = {}
        for prop_name, prop_schema in schema["properties"].items():
            resolved_property = resolve_schema(prop_schema, resolved_components, visited_refs, resolved_cache)
            if resolved_property is not None:
                # Ensure a deep copy is used to avoid circular references
                schema_copy["properties"][prop_name] = (
                    resolved_property.copy() if isinstance(resolved_property, dict) else resolved_property
                )
        return schema_copy

    # Handle array schemas
    if schema.get("type") == "array" and "items" in schema:
        schema_copy = schema.copy()
        resolved_items = resolve_schema(schema["items"], resolved_components, visited_refs, resolved_cache)
        if resolved_items is not None:
            schema_copy["items"] = resolved_items.copy() if isinstance(resolved_items, dict) else resolved_items
        return schema_copy

    # If no further resolution is needed, return the schema as-is
    return schema.copy() if isinstance(schema, dict) else schema


def parse_components(components: dict) -> dict:
    """
    Parses and resolves all $ref entries in the components section of the Swagger file.
    Handles OpenAPI 3.0 `components` and Swagger 2.0 `definitions` + `parameters`.

    :param components: The raw components section from the Swagger file.
    :return: A dictionary with resolved components.
    """
    resolved_components = {"schemas": {}, "parameters": {}}
    resolved_cache = {}  # Shared cache for all schemas

    for key, value in components.items():
        if isinstance(value, dict):
            resolved_components[key] = {}
            for sub_key, sub_value in value.items():
                resolved_schema = resolve_schema(sub_value, components, resolved_cache=resolved_cache)
                if resolved_schema is not None:
                    resolved_components[key][sub_key] = resolved_schema

    return resolved_components


def extract_parameter(param: dict) -> Parameter:
    """
    Extracts a Parameter object from a parameter dictionary using preprocessed components.

    :param param: Dictionary representing a parameter.
    :return: Parameter object with raw schema.
    """
    name = param.get("name", "")
    location = param.get("in", "")
    description = param.get("description", "")
    required = param.get("required", False)
    schema = param.get("schema", param)  # Default to param (for Swagger 2.0)
    custom_type = None

    # Extract custom type from $ref
    if "$ref" in schema:
        ref = schema["$ref"]
        custom_type = ref.split("/")[-1]

    default_value = schema.get("default", param.get("default", None))
    param_type = schema.get("type", "")
    if param_type == "array" and "items" in schema:
        items = schema["items"]
        default_value = items.get("default", default_value) or items.get("enum", [None])[0]

    return Parameter(
        name=name,
        description=description,
        location=location,
        required=required,
        param_type=param_type,
        param_format=schema.get("format", ""),
        nullable=schema.get("nullable", False),
        default=default_value,
        custom_type=custom_type,
        schema=schema  # Store raw schema
    )


def extract_request_body(request_body: dict):
    """
    Extracts parameters from a requestBody definition using preprocessed components.

    :param request_body: Dictionary representing the requestBody.
    :return: List of Parameter objects extracted from the requestBody.
    """
    parameters = []

    content = request_body.get("content", {})
    for media_type, media_details in content.items():
        schema = media_details.get("schema", {})  # Raw schema
        custom_type = None

        # Extract custom type from $ref
        if "$ref" in schema:
            ref = schema["$ref"]
            custom_type = ref.split("/")[-1]

        parameters.append(Parameter(
            name="body",
            description=f"Request body for {media_type}",
            location="body",
            required=request_body.get("required", False),
            param_type=schema.get("type", ""),  # Basic type (e.g., "object")
            param_format=schema.get("format", ""),  # Basic format (e.g., "int32")
            nullable=schema.get("nullable", False),
            default=None,
            media_type=media_type,
            custom_type=custom_type,
            schema=schema  # Store raw schema
        ))
    return parameters


default_string_values = {
    "date": "2024-01-01",
    "date-time": "2023-03-03T20:35:34.32",
    "email": "wapiti2021@mailinator.com",
    "uuid": str(uuid4()),
    "hostname": "google.com",
    "ipv4": "8.8.8.8",
    "ipv6": "2a00:1450:4007:818::200e",
    "uri": "https://example.com/api",
    "url": "https://example.com",
    "byte": "d2FwaXRp",
    "binary": "hello there",
    "password": "Letm3in_"
}


# pylint: disable=too-many-return-statements,too-many-branches
def generate_request_body_from_schema(
    schema: dict, resolved_components: dict, visited_refs: set = None
) -> Optional[RequestBody]:
    """
    Recursively generates a request body template from a given schema.

    :param schema: The raw schema to generate a body from.
    :param resolved_components: The resolved components dictionary.
    :param visited_refs: Tracks visited $refs to prevent infinite recursion.
    :return: A dictionary, list, or scalar representing a valid request body, or None if schema is empty.
    """
    if not schema:
        return None

    if visited_refs is None:
        visited_refs = set()

    # Handle $ref resolution
    if "$ref" in schema:
        ref = schema["$ref"]
        if ref in visited_refs:
            return None  # Skip circular references

        visited_refs.add(ref)
        ref_name = ref.split("/")[-1]
        resolved_schema = resolved_components["schemas"].get(ref_name, {})
        resolved_body = generate_request_body_from_schema(resolved_schema, resolved_components, visited_refs)
        visited_refs.remove(ref)

        return resolved_body

    schema_type = schema.get("type", "object")
    # Handle object schemas
    if schema_type == "object":
        result = {}
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            result[prop_name] = generate_request_body_from_schema(
                prop_schema, resolved_components, visited_refs
            )
            if prop_name in required_fields and result[prop_name] is None:
                result[prop_name] = "<required>"

        return result

    # Handle array schemas
    if schema_type == "array":
        items = schema.get("items", {})
        return [generate_request_body_from_schema(items, resolved_components, visited_refs)]

    # Handle enums
    if schema_type == "string" and "enum" in schema:
        return schema["enum"][0]  # Return the first enum value as an example

    # Handle scalar types
    if schema_type == "integer":
        return schema.get("default", 1)
    if schema_type == "number":
        return schema.get("default", 1.0)
    if schema_type == "boolean":
        return schema.get("default", True)
    if schema_type == "string":
        string_format = schema.get("format")
        return schema.get("default", default_string_values.get(string_format, "default"))

    # Fallback for unsupported types
    return f"<{schema_type or 'unknown'}>"
