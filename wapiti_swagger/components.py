"""Resolution of the `$ref` references found in the components of a Swagger (openAPI) file"""

import logging
from typing import Dict, Optional


def ref_name(schema: dict) -> Optional[str]:
    """
    Returns the name of the component a schema points to, or None if the schema is not a reference.

    Example: {"$ref": "#/components/schemas/Pet"} gives "Pet".
    """
    ref = schema.get("$ref")
    if not isinstance(ref, str):
        return None
    return ref.split("/")[-1]


def find_referenced_object(data: dict, ref: str) -> Optional[dict]:
    """
    Returns the object of the Swagger file a reference points to, or None if it can't be found.

    A reference is a JSON pointer: "#/components/parameters/limitParam" is the "limitParam" entry
    of the "parameters" section of the "components" section of the file.
    References to another file ("Pet.json", "https://example.com/api.yaml#/...") are not supported.

    :param data: The Swagger/OpenAPI specification as a dictionary.
    :param ref: The value of a `$ref` entry.
    """
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return None

    target = data
    for key in ref[2:].split("/"):
        # JSON pointer (RFC 6901) escape sequences, used for keys containing "/" or "~" such as paths
        key = key.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or key not in target:
            return None
        target = target[key]

    return target if isinstance(target, dict) else None


class SchemaResolver:  # pylint: disable=too-few-public-methods
    """
    Replaces the `$ref` references of a schema with the schema they point to.

    References can form loops (a `Node` schema having a `parent` property which is a `Node` too).
    A loop is cut at the place where it comes back to a reference whose resolution is not finished yet:
    there, the reference is considered unresolvable.
    """

    def __init__(self, schemas: Dict[str, dict]):
        """
        :param schemas: The raw (unresolved) schemas, by name.
        """
        self._schemas = schemas
        # Result of every reference met so far.
        # None means "unresolvable": unknown or empty schema, or resolution still in progress (loop).
        self._resolved_refs: Dict[str, Optional[dict]] = {}

    def resolve(self, schema: dict) -> Optional[dict]:
        """
        Returns a copy of the schema where references are replaced with the schema they point to.

        :return: The resolved schema, or None if the schema is a reference that can't be resolved.
        """
        if not schema or not isinstance(schema, dict):
            return schema

        if "$ref" in schema:
            return self._resolve_ref(schema)

        resolved = dict(schema)
        if schema.get("type") == "object" and "properties" in schema:
            resolved["properties"] = self._resolve_properties(schema["properties"])
        elif schema.get("type") == "array" and "items" in schema:
            resolved_items = self.resolve(schema["items"])
            # Unresolvable items are left untouched
            if resolved_items is not None:
                resolved["items"] = resolved_items
        return resolved

    def _resolve_properties(self, properties: Dict[str, dict]) -> Dict[str, dict]:
        """Resolves each property of an object, dropping the ones that can't be resolved."""
        resolved_properties = {}
        for name, property_schema in properties.items():
            resolved_property = self.resolve(property_schema)
            if resolved_property is not None:
                resolved_properties[name] = resolved_property
        return resolved_properties

    def _resolve_ref(self, schema: dict) -> Optional[dict]:
        """Returns the resolved version of the schema a reference points to, or None if it can't be resolved."""
        ref = schema["$ref"]

        if ref not in self._resolved_refs:
            # Until the resolution is over, the reference is unresolvable: this is what cuts the loops
            self._resolved_refs[ref] = None
            self._resolved_refs[ref] = self.resolve(self._schemas.get(ref_name(schema))) or None
        elif self._resolved_refs[ref] is None:
            logging.debug("Skipping unresolvable or circular reference: %s", ref)

        resolved = self._resolved_refs[ref]
        # Each use of a reference gets its own copy so that it can be modified independently
        return dict(resolved) if resolved else None


def resolve_schema(schema: dict, components: dict) -> Optional[dict]:
    """
    Resolves the `$ref` entries of a single schema.

    :param schema: The schema to resolve.
    :param components: The raw components, references are looked up in their "schemas" section.
    :return: The resolved schema, or None if the schema is a reference that can't be resolved.
    """
    return SchemaResolver(components.get("schemas", {})).resolve(schema)


def parse_components(components: dict) -> Dict[str, Dict[str, dict]]:
    """
    Resolves the `$ref` entries of every section ("schemas", "parameters"...) of the components.

    For Swagger 2.0 files, pass the `definitions` section as "schemas".

    :param components: The raw components section of the Swagger file.
    :return: The same sections, with resolved entries. Entries that can't be resolved are dropped.
    """
    # One resolver for all the sections, so that a reference used several times is resolved only once
    resolver = SchemaResolver(components.get("schemas", {}))
    resolved_components = {"schemas": {}, "parameters": {}}

    for section_name, section in components.items():
        if not isinstance(section, dict):
            continue

        resolved_components[section_name] = {}
        for name, schema in section.items():
            resolved = resolver.resolve(schema)
            if resolved is not None:
                resolved_components[section_name][name] = resolved

    return resolved_components
