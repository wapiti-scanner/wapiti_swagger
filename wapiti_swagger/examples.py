"""Generation of example values matching the schemas of a Swagger (openAPI) file"""

from typing import Any, Dict, List, Optional, Set, Union
from uuid import uuid4

from wapiti_swagger.components import ref_name

# What an example can be: a JSON-like value
RequestBody = Union[Dict[str, Any], List[Any], str, int, float, bool]

# Example value of a string, depending on its format
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
    "password": "Letm3in_",
}

# Example value of the other scalar types
default_scalar_values = {
    "integer": 1,
    "number": 1.0,
    "boolean": True,
}


class ExampleGenerator:  # pylint: disable=too-few-public-methods
    """
    Builds an example value for a schema, following its `$ref` references.

    References can form loops (a `Node` schema having a `parent` property which is a `Node` too).
    A loop is cut at the place where it comes back to a reference being generated: there, the value is None.
    """

    def __init__(self, schemas: Dict[str, dict]):
        """
        :param schemas: The schemas that references point to, by name.
        """
        self._schemas = schemas
        # References on the path from the root schema to the one being generated
        self._refs_in_progress: Set[str] = set()

    def generate(self, schema: Optional[dict]) -> Optional[RequestBody]:
        """Returns an example value for the schema, or None if there is nothing to generate."""
        if not schema:
            return None

        if "$ref" in schema:
            return self._generate_ref(schema)

        # A schema without type is considered an object
        schema_type = schema.get("type", "object")
        if schema_type == "object":
            return self._generate_object(schema)
        if schema_type == "array":
            return [self.generate(schema.get("items"))]
        return generate_scalar(schema_type, schema)

    def _generate_ref(self, schema: dict) -> Optional[RequestBody]:
        ref = schema["$ref"]
        if ref in self._refs_in_progress:
            return None  # Loop

        self._refs_in_progress.add(ref)
        example = self.generate(self._schemas.get(ref_name(schema)))
        self._refs_in_progress.remove(ref)
        return example

    def _generate_object(self, schema: dict) -> Dict[str, Any]:
        required_properties = schema.get("required", [])
        example = {}
        for name, property_schema in schema.get("properties", {}).items():
            value = self.generate(property_schema)
            if value is None and name in required_properties:
                value = "<required>"
            example[name] = value
        return example


def generate_scalar(schema_type: Any, schema: dict) -> RequestBody:
    """Returns an example value for a schema which is neither an object nor an array."""
    if schema_type == "string":
        if schema.get("enum"):
            return schema["enum"][0]
        return schema.get("default", default_string_values.get(schema.get("format"), "default"))

    # OpenAPI 3.1 allows a list of types, which can't be looked up
    if isinstance(schema_type, str) and schema_type in default_scalar_values:
        return schema.get("default", default_scalar_values[schema_type])

    # Unsupported type ("file"...): a placeholder
    return f"<{schema_type or 'unknown'}>"


def generate_request_body_from_schema(schema: Optional[dict], resolved_components: dict) -> Optional[RequestBody]:
    """
    Generates an example request body from a schema.

    :param schema: The schema to generate a body from, typically the `schema` attribute of a Parameter.
    :param resolved_components: The components of the Swagger file (`ParsedSwagger.components`),
                                references are looked up in their "schemas" section.
    :return: A dictionary, list, or scalar representing a valid request body, or None if the schema is empty.
    """
    return ExampleGenerator(resolved_components.get("schemas", {})).generate(schema)
