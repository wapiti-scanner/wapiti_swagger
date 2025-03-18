import pytest

from wapiti_swagger.parser import parse

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
