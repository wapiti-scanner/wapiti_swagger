import pytest

from wapiti_swagger.parser import extract_requests, parse

# Save the complex Swagger file content as a string
MISSING_PATH_SWAGGER = """
{
    "openapi": "3.0.0",
    "info": {
      "version": "1.0.0",
      "title": "Swagger Petstore",
      "license": {
        "name": "MIT"
      }
    },
    "servers": [
      {
        "url": "http://petstore.swagger.io/v1"
      }
    ]
  }
"""

@pytest.fixture(name="missing_paths")
def complex_swagger_file(tmp_path):
    swagger_path = tmp_path / "missing_paths.json"
    swagger_path.write_text(MISSING_PATH_SWAGGER)
    return swagger_path


def test_generate_request_body_with_complex_object(missing_paths):
    # Parse the Swagger file
    with pytest.raises(ValueError):
        parse(str(missing_paths))


def test_parse_rejects_unsupported_extension(tmp_path):
    swagger_path = tmp_path / "swagger.txt"
    swagger_path.write_text('{"paths": {}}')
    with pytest.raises(ValueError, match="Unsupported file format"):
        parse(str(swagger_path))


@pytest.mark.parametrize("extension", ["yaml", "yml"])
def test_parse_yaml_file(tmp_path, extension):
    swagger_path = tmp_path / f"swagger.{extension}"
    swagger_path.write_text(
        "swagger: '2.0'\n"
        "host: api.example.com\n"
        "paths:\n"
        "  /pets:\n"
        "    get:\n"
        "      summary: List pets\n"
    )
    parsed = parse(str(swagger_path))
    assert [(request.method, request.path) for request in parsed.requests] == [("GET", "/pets")]
    assert parsed.urls() == ["http://api.example.com"]
    assert not parsed.components


def test_extract_requests_rejects_missing_paths():
    with pytest.raises(ValueError, match="'paths' section is missing"):
        extract_requests({"openapi": "3.0.0"})
