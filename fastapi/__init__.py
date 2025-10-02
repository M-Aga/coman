"""Lightweight FastAPI-compatible stubs for tests."""
from .app import FastAPI
from .routing import APIRouter
from .exceptions import HTTPException
from .params import Body

__all__ = ["FastAPI", "APIRouter", "HTTPException", "Body"]
