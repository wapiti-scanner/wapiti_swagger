"""Module containing structs to handle Swagger (openAPI) elements"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# pylint: disable=too-few-public-methods
class Parameter:
    """Represents a parameter expected by an API endpoint"""
    # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        name: str,
        description: str = "",
        location: str = "",
        required: bool = False,
        param_type: str = "",
        param_format: str = "",
        nullable: bool = False,
        default=None,
        media_type: str = None,
        custom_type: str = None,
        schema: dict = None,  # Add schema attribute
    ):
        """
        Initialize a parameter object with its relevant details.

        :param schema: The full schema definition for the parameter.
        """
        self.name = name
        self.description = description
        self.location = location
        self.required = required
        self.param_type = param_type
        self.param_format = param_format
        self.nullable = nullable
        self.default = default
        self.media_type = media_type
        self.custom_type = custom_type
        self.schema = schema or {}

    def __repr__(self):
        return (
            f"<Parameter {self.name} ({self.location}) required={self.required} "
            f"type={self.param_type} format={self.param_format} nullable={self.nullable} "
            f"default={self.default} media_type={self.media_type} custom_type={self.custom_type}>"
        )



class SwaggerRequest:
    """Represents HTTP request information required to use an API endpoint"""
    # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
    def __init__(
            self,
            path: str,
            method: str,
            summary: str,
            parameters: list[Parameter],
            consumes: Optional[List[str]]
    ):
        self.path = path
        self.method = method
        self.summary = summary
        self.parameters = parameters
        self.consumes = consumes if consumes is not None else []

    def __repr__(self):
        output = ""
        if self.summary:
            output = self.summary + "\n"
        output += f"{self.method} {self.path}\n"
        output += str(self.parameters) + "\n"
        return output


@dataclass
class ParsedSwagger:
    """Represents the various sections of a swagger (openAPI) file"""
    metadata: Dict[str, Any]
    requests: List[SwaggerRequest]
    components: Dict[str, Dict]

    def urls(self) -> List[str]:
        """
        Returns the list of full URLs for the API, combining host, basePath, schemes, or servers.
        """
        urls = []

        # Swagger 2.0: Combine schemes, host, and basePath
        if self.metadata:
            host = self.metadata.get("host")
            base_path = self.metadata.get("basePath", "").rstrip("/")
            # Default to http if schemes not provided
            schemes = self.metadata.get("schemes", ["http"])

            if host:
                for scheme in schemes:
                    urls.append(f"{scheme}://{host}{base_path}")

            # OpenAPI 3.x: Use servers directly
            servers = self.metadata.get("servers")
            if servers:
                urls.extend(servers)

        return [url for url in urls if url.strip()]
