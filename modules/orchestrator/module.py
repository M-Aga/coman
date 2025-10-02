from __future__ import annotations
from coman.core.base_module import BaseModule
from coman.core.messages import Capability, CapabilityRegistry
from fastapi import Body, HTTPException
import os, json, importlib.util, glob
CAP_PATH = os.path.join("coman","data","capabilities.json")


def load_caps() -> CapabilityRegistry:
    if not os.path.exists(CAP_PATH):
        return CapabilityRegistry()
    with open(CAP_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CapabilityRegistry.from_payload(data)


def save_caps(registry: CapabilityRegistry) -> None:
    os.makedirs(os.path.dirname(CAP_PATH), exist_ok=True)
    with open(CAP_PATH, "w", encoding="utf-8") as f:
        json.dump(registry.to_payload(), f, ensure_ascii=False, indent=2)
class Module(BaseModule):
    name = "orchestrator"; description = "LLM router + capability registry + extensions loader"
    def __init__(self, core):
        super().__init__(core)
        @self.router.get("/capabilities")
        def capabilities():
            return load_caps().to_payload()
        @self.router.post("/capabilities/register")
        def cap_register(
            payload: Capability | None = Body(default=None),
            name: str | None = None,
            kind: str = "webhook",
            endpoint: str = "",
            description: str = "",
        ):
            registry = load_caps()
            if payload is not None:
                cap = Capability.from_payload(payload)
            else:
                cap = Capability(name=name or "", kind=kind, endpoint=endpoint, description=description)
            if not cap.name:
                raise HTTPException(400, "name is required")
            registry.add(cap)
            save_caps(registry)
            return {"ok": True, "count": len(registry.capabilities)}
        @self.router.post("/extensions/reload")
        def reload_ext(dir_path: str = "./extensions"):
            loaded = []
            for path in glob.glob(os.path.join(dir_path, "*.py")):
                spec = importlib.util.spec_from_file_location(os.path.basename(path).rsplit(".",1)[0], path)
                if not spec or not spec.loader: continue
                mod = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "register"): mod.register(self.core); loaded.append(os.path.basename(path))
                except Exception as e:
                    loaded.append(f"{os.path.basename(path)}:error:{e}")
            return {"loaded": loaded}
