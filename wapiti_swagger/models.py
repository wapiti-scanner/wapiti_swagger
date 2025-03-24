"""Module containing structs to handle Swagger (openAPI) elements"""
from typing import Any, Dict, List, Optional


from dataclasses import dataclass, field


# pylint: disable=too-many-instance-attributes
@dataclass
class Parameter:
    """Represents a parameter expected by an API endpoint"""
    name: str
    description: str = ""
    location: str = ""
    required: bool = False
    param_type: str = ""
    param_format: str = ""
    nullable: bool = False
    default: Any = None
    media_type: Optional[str] = None
    custom_type: Optional[str] = None
    schema: dict = field(default_factory=dict)  # Use `field` to avoid mutable default


class SwaggerRequest:
    """Represents HTTP request information required to use an API endpoint"""
    # pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments,too-few-public-methods
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
