from __future__ import annotations
from coman.core.base_module import BaseModule
from coman.core.config import settings
import os, json, importlib.util, glob
CAP_PATH = os.path.join("coman","data","capabilities.json")
def load_caps():
    if not os.path.exists(CAP_PATH): return {"capabilities": []}
    with open(CAP_PATH,"r",encoding="utf-8") as f: return json.load(f)
def save_caps(data):
    os.makedirs(os.path.dirname(CAP_PATH), exist_ok=True)
    with open(CAP_PATH,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
class Module(BaseModule):
    name = "orchestrator"; description = "LLM router + capability registry + extensions loader"
    def __init__(self, core):
        super().__init__(core)
        @self.router.get("/capabilities")
        def capabilities(): return load_caps()
        @self.router.post("/capabilities/register")
        def cap_register(
            name: str,
            kind: str = "webhook",
            endpoint: str = "",
            description: str = "",
            original_name: str | None = None,
        ):
            target_names = {name}
            if original_name:
                target_names.add(original_name)
            data = load_caps()
            data["capabilities"] = [x for x in data["capabilities"] if x.get("name") not in target_names]
            data["capabilities"].append({
                "name": name,
                "kind": kind,
                "endpoint": endpoint,
                "description": description,
            })
            save_caps(data)
            return {"ok": True, "count": len(data["capabilities"])}
        @self.router.post("/capabilities/delete")
        def cap_delete(name: str):
            data = load_caps()
            before = len(data.get("capabilities", []))
            data["capabilities"] = [x for x in data["capabilities"] if x.get("name") != name]
            save_caps(data)
            return {"ok": True, "deleted": before - len(data["capabilities"])}
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
