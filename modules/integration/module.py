from __future__ import annotations
from coman.core.base_module import BaseModule
from coman.core.config import settings
from fastapi import HTTPException
import sys, os, json, importlib, subprocess
REG_PATH = os.path.join("coman","data","integrations.json")
def load_reg():
    if not os.path.exists(REG_PATH): return {"integrations":[]}
    with open(REG_PATH,"r",encoding="utf-8") as f: return json.load(f)
def save_reg(data):
    os.makedirs(os.path.dirname(REG_PATH), exist_ok=True)
    with open(REG_PATH,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
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
        def register(name: str, path: str, module: str, callable: str):
            if not _is_allowed(path):
                raise HTTPException(400, f"path '{path}' is not in allowed list: {settings.allowed_integration_paths}")
            if path not in sys.path: sys.path.append(path)
            mod = importlib.import_module(module); getattr(mod, callable)
            sig = _sha256(_module_file(module))
            data = load_reg()
            data["integrations"] = [x for x in data["integrations"] if x.get("name") != name]
            data["integrations"].append({"name":name,"path":path,"module":module,"callable":callable,"sig":sig})
            save_reg(data); return {"ok": True, "sig": sig}
        @self.router.get("/list")
        def listing(): return load_reg()
        @self.router.post("/call")
        def call(name: str, callable: str | None = None, kwargs: dict | None = None, mode: str = "inproc", verify_sig: int = 1):
            data = load_reg(); it = next((x for x in data["integrations"] if x["name"] == name), None)
            if not it: raise HTTPException(404, "integration not found")
            if not _is_allowed(it["path"]): raise HTTPException(400, f"path '{it['path']}' is not allowed anymore")
            if it["path"] not in sys.path: sys.path.append(it["path"])
            if verify_sig:
                cur = _sha256(_module_file(it["module"]))
                if cur and cur != it.get("sig",""): raise HTTPException(400, "signature mismatch")
            if kwargs is None: kwargs = {}
            if not isinstance(kwargs, dict):
                raise HTTPException(400, "kwargs must be a JSON object")
            if "kwargs" in kwargs and len(kwargs) == 1 and isinstance(kwargs["kwargs"], dict):
                kwargs = kwargs["kwargs"]
            target_callable = callable or it.get("callable")
            if not target_callable:
                raise HTTPException(400, "callable not specified")
            module_name = it["module"]
            func_name = target_callable
            if "." in target_callable:
                mod_part, func_part = target_callable.rsplit(".", 1)
                if mod_part != module_name:
                    raise HTTPException(400, "callable must belong to the registered module")
                module_name, func_name = mod_part, func_part
            if mode == "inproc":
                mod = importlib.import_module(module_name)
                fn = getattr(mod, func_name)
                return {"result": fn(**kwargs)}
            else:
                runner = os.path.join(os.path.dirname(__file__), "runner.py")
                payload = json.dumps({"module": module_name, "callable": func_name, "kwargs": kwargs})
                proc = subprocess.run([sys.executable, runner], input=payload, text=True, capture_output=True, timeout=30)
                import json as _json
                try: resp = _json.loads(proc.stdout)
                except Exception: resp = {"ok": False, "stdout": proc.stdout, "stderr": proc.stderr}
                return resp
        @self.router.post("/scaffold")
        def scaffold(name: str, target_dir: str):
            os.makedirs(target_dir, exist_ok=True)
            file = os.path.join(target_dir, f"{name}_adapter.py")
            with open(file,"w",encoding="utf-8") as f: f.write("def run(**kwargs):\n    return {'ok': True, 'kwargs': kwargs}\n")
            return {"created": file}
