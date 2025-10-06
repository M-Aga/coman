from __future__ import annotations
from pathlib import Path

from coman.core.base_module import BaseModule
from coman.core.config import settings
from coman.core.messages import (
    IntegrationCallRequest,
    IntegrationCallResult,
    IntegrationDefinition,
    IntegrationRegistry,
)
from fastapi import Body, HTTPException
import sys, os, json, importlib, subprocess


def _reg_path() -> Path:
    return Path(settings.data_dir) / "integrations.json"


def load_reg() -> IntegrationRegistry:
    path = _reg_path()
    if not path.exists():
        return IntegrationRegistry()
    with path.open("r", encoding="utf-8-sig") as f:
        raw_text = f.read()

    if not raw_text.strip():
        return IntegrationRegistry()

    data = json.loads(raw_text)
    return IntegrationRegistry.from_payload(data)


def save_reg(registry: IntegrationRegistry) -> None:
    path = _reg_path()
    os.makedirs(path.parent, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(registry.to_payload(), f, ensure_ascii=False, indent=2)
def _is_allowed(path: str) -> bool:
    rp = os.path.realpath(path)
    for base in settings.allowed_integration_paths:
        rb = os.path.realpath(base)
        try:
            if rp == rb or rp.startswith(rb + os.sep): return True
        except Exception: pass
    return False
def _module_file(module: str):
    try:
        mod = importlib.import_module(module); return getattr(mod, "__file__", None)
    except Exception: return None
def _sha256(p: str):
    import hashlib
    if not p or not os.path.exists(p): return ""
    h = hashlib.sha256()
    with open(p,"rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()
class Module(BaseModule):
    name = "integration"; description = "Register and call external python code by source path (secure)"
    def __init__(self, core):
        super().__init__(core)
        @self.router.post("/register")
        def register(
            payload: IntegrationDefinition | None = Body(default=None),
            name: str | None = None,
            path: str | None = None,
            module: str | None = None,
            callable: str | None = None,
        ):
            if payload is not None:
                data = IntegrationDefinition.from_payload(payload)
            else:
                if not all([name, path, module, callable]):
                    raise HTTPException(400, "name, path, module and callable are required")
                data = IntegrationDefinition(name=name or "", path=path or "", module=module or "", callable=callable or "")

            if not _is_allowed(data.path):
                raise HTTPException(400, f"path '{data.path}' is not in allowed list: {settings.allowed_integration_paths}")
            if data.path not in sys.path:
                sys.path.append(data.path)
            mod = importlib.import_module(data.module)
            getattr(mod, data.callable)
            sig = _sha256(_module_file(data.module))
            registry = load_reg()
            data.sig = sig
            registry.upsert(data)
            save_reg(registry)
            return {"ok": True, "sig": sig}
        @self.router.get("/list")
        def listing():
            return load_reg().to_payload()
        @self.router.post("/call")
        def call(
            name: str,
            callable: str | None = None,
            kwargs: dict | None = None,
            mode: str = "inproc",
            verify_sig: int = 1,
        ):
            registry = load_reg()
            integration = registry.find(name)
            if not integration:
                raise HTTPException(404, "integration not found")
            if not _is_allowed(integration.path):
                raise HTTPException(400, f"path '{integration.path}' is not allowed anymore")
            if integration.path not in sys.path:
                sys.path.append(integration.path)
            raw_kwargs = kwargs or {}
            if not isinstance(raw_kwargs, dict):
                raise HTTPException(400, "kwargs must be a JSON object")
            req = IntegrationCallRequest(
                name=name,
                callable=callable,
                kwargs=raw_kwargs,
                mode=mode,
                verify_sig=bool(verify_sig),
            )
            if req.verify_sig:
                cur = _sha256(_module_file(integration.module))
                if cur and cur != (integration.sig or ""):
                    raise HTTPException(400, "signature mismatch")
            call_kwargs = req.kwargs or {}
            target_callable = req.callable or integration.callable
            if not target_callable:
                raise HTTPException(400, "callable not specified")
            module_name = integration.module
            func_name = target_callable
            if "." in target_callable:
                mod_part, func_part = target_callable.rsplit(".", 1)
                if mod_part != module_name:
                    raise HTTPException(400, "callable must belong to the registered module")
                module_name, func_name = mod_part, func_part
            if req.mode == "inproc":
                mod = importlib.import_module(module_name)
                fn = getattr(mod, func_name)
                return IntegrationCallResult(result=fn(**call_kwargs)).to_payload()
            runner = os.path.join(os.path.dirname(__file__), "runner.py")
            payload = json.dumps({"module": module_name, "callable": func_name, "kwargs": call_kwargs})
            proc = subprocess.run([sys.executable, runner], input=payload, text=True, capture_output=True, timeout=30)
            import json as _json

            try:
                resp = _json.loads(proc.stdout)
            except Exception:
                resp = IntegrationCallResult(ok=False, stdout=proc.stdout, stderr=proc.stderr).to_payload()
            else:
                return resp
            return resp
        @self.router.post("/scaffold")
        def scaffold(name: str, target_dir: str):
            os.makedirs(target_dir, exist_ok=True)
            file = os.path.join(target_dir, f"{name}_adapter.py")
            with open(file,"w",encoding="utf-8") as f: f.write("def run(**kwargs):\n    return {'ok': True, 'kwargs': kwargs}\n")
            return {"created": file}
