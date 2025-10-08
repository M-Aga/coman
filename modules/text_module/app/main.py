"""Standalone FastAPI application for the text utility module."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from observability import instrument_fastapi_app, setup_module_observability


class UppercaseRequest(BaseModel):
    """Request payload for the uppercase transformation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., description="Arbitrary text that will be converted to uppercase.")

    @field_validator("text")
    @classmethod
    def _ensure_not_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "text must contain at least one visible character"
            raise ValueError(msg)
        return value


class UppercaseResponse(BaseModel):
    """Response schema for the uppercase transformation."""

    original: str
    uppercased: str


SERVICE_NAME = "text"

router = APIRouter(prefix="/v1/text", tags=["text"])
setup_module_observability(SERVICE_NAME, "1.0.0", router=router)


@router.post("/uppercase", response_model=UppercaseResponse, summary="Uppercase a string")
async def uppercase(payload: UppercaseRequest) -> UppercaseResponse:
    """Return the uppercased form of the provided string."""

    result = payload.text.upper()
    return UppercaseResponse(original=payload.text, uppercased=result)


LEGACY_SUNSET = date(2025, 9, 30)
legacy_router = APIRouter(prefix="/text", tags=["text"], deprecated=True)
setup_module_observability(SERVICE_NAME, "1.0.0", router=legacy_router)


@legacy_router.get(
    "/uppercase",
    response_model=UppercaseResponse,
    summary="[Deprecated] Uppercase a string",
    deprecated=True,
    openapi_extra={"sunset": LEGACY_SUNSET.isoformat()},
)
async def legacy_uppercase(text: str) -> UppercaseResponse:
    """Compatibility shim for the previous query parameter based endpoint."""

    request = UppercaseRequest(text=text)
    return await uppercase(request)


app = FastAPI(
    title="Text Module API",
    version="1.0.0",
    summary="Utility endpoints for text processing.",
    docs_url="/docs",
    redoc_url="/redoc",
)
instrument_fastapi_app(app, module_name=SERVICE_NAME, module_version="1.0.0")
app.include_router(router)
app.include_router(legacy_router)


@app.get("/openapi.json", include_in_schema=False)
async def openapi_document() -> JSONResponse:
    """Expose the OpenAPI schema for tooling downloads."""

    return JSONResponse(app.openapi())
