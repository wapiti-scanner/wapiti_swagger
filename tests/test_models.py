from wapiti_swagger.models import Parameter, ParsedSwagger, SwaggerRequest


def make_swagger(metadata):
    return ParsedSwagger(metadata=metadata, requests=[], components={})


def test_urls_swagger2_combines_schemes_host_and_base_path():
    swagger = make_swagger({"host": "api.example.com", "basePath": "/v2/", "schemes": ["http", "https"]})
    assert swagger.urls() == ["http://api.example.com/v2", "https://api.example.com/v2"]


def test_urls_swagger2_defaults_to_http_without_base_path():
    swagger = make_swagger({"host": "api.example.com"})
    assert swagger.urls() == ["http://api.example.com"]


def test_urls_openapi3_uses_servers():
    swagger = make_swagger({"servers": ["https://a.example.com/v1", "https://b.example.com"]})
    assert swagger.urls() == ["https://a.example.com/v1", "https://b.example.com"]


def test_urls_combines_host_and_servers_and_skips_blank_entries():
    swagger = make_swagger({"host": "api.example.com", "schemes": ["https"], "servers": ["  ", "https://other.com"]})
    assert swagger.urls() == ["https://api.example.com", "https://other.com"]


def test_urls_without_metadata():
    assert make_swagger({}).urls() == []
    assert make_swagger({"servers": []}).urls() == []


def test_swagger_request_repr():
    parameter = Parameter(name="id", location="query", param_type="integer")
    request = SwaggerRequest(path="/pets", method="GET", summary="List pets", parameters=[parameter], consumes=None)

    output = repr(request)
    assert output.startswith("List pets\nGET /pets\n")
    assert "name='id'" in output
    assert request.consumes == []

    no_summary = SwaggerRequest(path="/pets", method="POST", summary="", parameters=[], consumes=["application/json"])
    assert repr(no_summary) == "POST /pets\n[]\n"
    assert no_summary.consumes == ["application/json"]
