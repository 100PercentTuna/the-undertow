"""
OpenAPI schema routes.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

router = APIRouter(tags=["Documentation"])


@router.get("/schema.json")
async def get_openapi_json() -> JSONResponse:
    """
    Get OpenAPI schema in JSON format.

    This can be used for code generation, documentation,
    or API client auto-configuration.
    """
    from undertow.api.main import app

    return JSONResponse(content=app.openapi())


@router.get("/schema.yaml")
async def get_openapi_yaml() -> Response:
    """
    Get OpenAPI schema in YAML format.

    Requires PyYAML to be installed.
    """
    try:
        import yaml
    except ImportError:
        return Response(
            content="PyYAML not installed",
            status_code=500,
            media_type="text/plain",
        )

    from undertow.api.main import app

    schema = app.openapi()
    yaml_content = yaml.dump(schema, default_flow_style=False, allow_unicode=True)

    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
    )

