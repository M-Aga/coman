import importlib, pkgutil
from typing import Dict, Type
from .base_module import BaseModule
class Core:
    def __init__(self):
        self.modules: Dict[str, BaseModule] = {}
        self.scheduler = None
def load_modules(core: Core):
    pkg = importlib.import_module("coman.modules")
    for info in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        if not info.ispkg:
            continue
        modname = f"{info.name}.module"
        try:
            module = importlib.import_module(modname)
            cls: Type[BaseModule] = getattr(module, "Module", None)
            if not cls:
                print(f"[load_modules] skip {modname}: no Module class"); continue
            inst = cls(core)
            core.modules[inst.name] = inst
            print(f"[load_modules] loaded {inst.name} from {modname}")
        except Exception as e:
            print(f"[load_modules] skip {modname}: {e}")
            continue
