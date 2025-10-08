"""Standalone FastAPI application for the analysis module."""

from __future__ import annotations

from collections import Counter
from datetime import date

from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator


class FrequencyRequest(BaseModel):
    """Request payload for the /frequency endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., description="Arbitrary text that will be tokenised by whitespace.")

    @field_validator("text")
    @classmethod
    def _ensure_not_blank(cls, value: str) -> str:
        if not value.strip():
            msg = "text must contain at least one non-whitespace character"
            raise ValueError(msg)
        return value


class FrequencyResponse(BaseModel):
    """Response schema describing token counts."""

    counts: dict[str, int]


router = APIRouter(prefix="/v1/analysis", tags=["analysis"])


@router.post("/frequency", response_model=FrequencyResponse, summary="Count token frequency")
async def frequency(payload: FrequencyRequest) -> FrequencyResponse:
    """Return a case-insensitive word frequency map for the provided text."""

    tokens = [token.lower() for token in payload.text.split() if token.strip()]
    return FrequencyResponse(counts=dict(Counter(tokens)))


LEGACY_SUNSET = date(2025, 3, 31)
legacy_router = APIRouter(prefix="/analysis", tags=["analysis"], deprecated=True)


@legacy_router.post(
    "/frequency",
    response_model=FrequencyResponse,
    summary="[Deprecated] Count token frequency",
    deprecated=True,
    openapi_extra={"sunset": LEGACY_SUNSET.isoformat()},
)
async def legacy_frequency(payload: FrequencyRequest) -> FrequencyResponse:
    """Compatibility shim for the previous un-versioned endpoint."""

    response = await frequency(payload)
    return response


app = FastAPI(
    title="Analysis Module API",
    version="1.0.0",
    summary="Provides text token frequency statistics.",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.include_router(router)
app.include_router(legacy_router)


@app.get("/openapi.json", include_in_schema=False)
async def openapi_document() -> JSONResponse:
    """Expose the OpenAPI document explicitly for tooling downloads."""

    return JSONResponse(app.openapi())
