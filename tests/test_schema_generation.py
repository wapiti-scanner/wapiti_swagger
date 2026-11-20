import pytest

from wapiti_swagger.parser import default_string_values, generate_request_body_from_schema

NO_COMPONENTS = {"schemas": {}}


@pytest.mark.parametrize(
    "schema, expected",
    [
        ({"type": "integer"}, 1),
        ({"type": "integer", "default": 7}, 7),
        ({"type": "number"}, 1.0),
        ({"type": "number", "default": 2.5}, 2.5),
        ({"type": "boolean"}, True),
        ({"type": "boolean", "default": False}, False),
        ({"type": "string"}, "default"),
        ({"type": "string", "default": "foo"}, "foo"),
        ({"type": "string", "format": "email"}, default_string_values["email"]),
        ({"type": "string", "format": "unknown-format"}, "default"),
        ({"type": "string", "enum": ["red", "green"]}, "red"),
        ({"type": "file"}, "<file>"),
        ({"type": ""}, "<unknown>"),
    ],
)
def test_generate_scalar_values(schema, expected):
    assert generate_request_body_from_schema(schema, NO_COMPONENTS) == expected


def test_generate_empty_schema_returns_none():
    assert generate_request_body_from_schema({}, NO_COMPONENTS) is None
    assert generate_request_body_from_schema(None, NO_COMPONENTS) is None


def test_generate_object_defaults_to_object_type():
    schema = {"properties": {"age": {"type": "integer"}}}
    assert generate_request_body_from_schema(schema, NO_COMPONENTS) == {"age": 1}


def test_generate_array():
    schema = {"type": "array", "items": {"type": "string", "format": "ipv4"}}
    assert generate_request_body_from_schema(schema, NO_COMPONENTS) == ["8.8.8.8"]

    # Array without items: the item schema is empty
    assert generate_request_body_from_schema({"type": "array"}, NO_COMPONENTS) == [None]


def test_generate_marks_empty_required_fields():
    schema = {
        "type": "object",
        "required": ["blob", "name"],
        "properties": {
            "blob": {},
            "name": {"type": "string"},
            "optional": {},
        },
    }
    assert generate_request_body_from_schema(schema, NO_COMPONENTS) == {
        "blob": "<required>",
        "name": "default",
        "optional": None,
    }


def test_generate_breaks_circular_references():
    components = {
        "schemas": {
            "Node": {
                "type": "object",
                "required": ["parent"],
                "properties": {
                    "name": {"type": "string"},
                    "parent": {"$ref": "#/components/schemas/Node"},
                    "children": {"type": "array", "items": {"$ref": "#/components/schemas/Node"}},
                },
            }
        }
    }

    body = generate_request_body_from_schema({"$ref": "#/components/schemas/Node"}, components)
    assert body == {"name": "default", "parent": "<required>", "children": [None]}


def test_generate_reuses_same_reference_in_siblings():
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

    body = generate_request_body_from_schema({"$ref": "#/components/schemas/Order"}, components)
    assert body == {"billing": {"city": "default"}, "shipping": {"city": "default"}}


def test_generate_unknown_reference_returns_none():
    assert generate_request_body_from_schema({"$ref": "#/components/schemas/Missing"}, NO_COMPONENTS) is None
