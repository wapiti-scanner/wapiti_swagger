# **Wapiti Swagger Parser**

![License](https://img.shields.io/github/license/wapiti-scanner/wapiti_swagger)
![Python Versions](https://img.shields.io/badge/python-3.8%20|%203.9%20|%203.10%20|%203.11%20|%203.12-blue)

## **Project Description**

The **Wapiti Swagger Parser** is a Python library designed to parse Swagger (OpenAPI) specifications and extract the necessary information to generate valid HTTP requests. It focuses on providing a clean, programmatic interface for analyzing Swagger files and creating request templates without relying on external tools for OpenAPI processing.

This library is particularly useful for scenarios where only the request generation requirements are of interest, such as:

- Automated testing and validation of APIs.
- Dynamic request generation for web vulnerability scanners (like Wapiti).
- Custom API tooling.

The library is lightweight, relying only on Python's built-in `json` library and `PyYAML` for file parsing, and it avoids heavy dependencies on larger OpenAPI frameworks.

---

## **Key Features**

- **Request Extraction**:
  - Parses all HTTP requests (methods, paths, parameters) defined in the Swagger file.
- **Schema Handling**:
  - Resolves `$ref` references in schemas, including handling circular references gracefully.
- **Custom Types**:
  - Identifies and retains custom types (e.g., enumerated values, objects) for enhanced request understanding.
- **Request Body Generation**:
  - Automatically generates example request bodies based on schema definitions.
- **Metadata Extraction**:
  - Captures root-level metadata like `host`, `basePath`, `servers`, and `schemes`.
- **Supports Swagger 2.0 and OpenAPI 3.x**:
  - Works with both specification versions seamlessly.

---

## **Usage Example**

```python
from wapiti_swagger.parser import parse, generate_request_body_from_schema

# Load and parse a Swagger file
parsed = parse("swagger.json")

# List all available requests
for request in parsed.requests:
    print(request)

# Generate an example request body for a specific request (here one expecting JSON input)
request_body = generate_request_body_from_schema(
    schema=request.parameters[0].schema,  # Use the schema of the first parameter
    resolved_components=parsed.components
)
print("Example request body:", request_body)
```

---

## **Why Use This Library?**

Unlike general-purpose OpenAPI parsers, this library is optimized for specific use cases like generating valid requests for API testing, scanning, or mocking. It is lightweight, customizable, and avoids unnecessary processing of response definitions or additional metadata unrelated to request generation.

---

## **Methods in `parser` Module**

### 1. `parse(file_path: str) -> ParsedSwagger`  
Parses a Swagger/OpenAPI specification file and returns a `ParsedSwagger` object containing the following:  
- **Requests:** List of `SwaggerRequest` objects extracted from paths.
- **Components:** Preprocessed and resolved components (e.g., schemas, parameters).
- **Metadata:** High-level metadata like `host`, `basePath`, and `servers`.

**Parameters:**
- `file_path` (str): Path to the Swagger/OpenAPI file (JSON or YAML).

**Returns:**
- `ParsedSwagger`: Object containing parsed requests, components, and metadata.

---

### 2. `extract_requests(data: dict) -> List[SwaggerRequest]`  
Extracts all HTTP requests from the `paths` section of the Swagger specification.

**Parameters:**
- `data` (dict): The full Swagger/OpenAPI specification as a dictionary.

**Returns:**
- `List[SwaggerRequest]`: A list of requests with details like method, path, parameters, and request bodies.

---

### 3. `extract_request_body(request_body: dict) -> List[Parameter]`  
Extracts parameters from the `requestBody` section of a Swagger path operation.  
Handles multiple media types (e.g., `application/json`, `text/json`).

**Parameters:**
- `request_body` (dict): The `requestBody` definition for a path operation.

**Returns:**
- `List[Parameter]`: A list of parameters with details like media type, schema, and custom type.

---

### 4. `extract_parameter(param: dict) -> Parameter`  
Parses a single parameter from the `parameters` section of a Swagger path operation.

**Parameters:**
- `param` (dict): The parameter definition.

**Returns:**
- `Parameter`: Object representing the parameter with details like name, location, type, and schema.

---

### 5. `parse_components(components: dict) -> Dict[str, Dict]`  
Resolves and preprocesses all components (e.g., schemas, parameters) from the `components` section of the Swagger specification.

**Parameters:**
- `components` (dict): The `components` section of the Swagger specification.

**Returns:**
- `Dict[str, Dict]`: Resolved and preprocessed components organized by type (e.g., schemas, parameters).

---

### 6. `resolve_schema(schema: dict, resolved_components: dict, visited_refs: set) -> dict`  
Recursively resolves `$ref` references in schemas while avoiding circular references.

**Parameters:**
- `schema` (dict): The schema to resolve.
- `resolved_components` (dict): Preprocessed components for reference resolution.
- `visited_refs` (set): Tracks references to avoid circular references.

**Returns:**
- `dict`: Fully resolved schema.

---

### 7. `extract_metadata(data: dict) -> Dict[str, Any]`  
Extracts high-level metadata from the root of the Swagger specification, such as `host`, `basePath`, and `servers`.

**Parameters:**
- `data` (dict): The full Swagger/OpenAPI specification.

**Returns:**
- `Dict[str, Any]`: Metadata like `host`, `basePath`, `schemes`, and `servers`.

---

### 8. `generate_request_body_from_schema(schema: dict, resolved_components: dict) -> Optional[Union[dict, list, str, int, bool]]`  
Generates an example request body based on a schema definition.

**Parameters:**
- `schema` (dict): The schema definition.
- `resolved_components` (dict): Resolved components for reference resolution.

**Returns:**
- `Optional[Union[dict, list, str, int, bool]]`: An example request body.

---
