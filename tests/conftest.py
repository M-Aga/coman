import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force-load the repository's telegram shim so ``telegram.coman`` stays available.
for key in list(sys.modules):
    if key == "telegram" or key.startswith("telegram."):
        sys.modules.pop(key, None)

spec = importlib.util.spec_from_file_location("telegram", ROOT / "telegram" / "__init__.py")
if spec and spec.loader:
    module = importlib.util.module_from_spec(spec)
    sys.modules["telegram"] = module
    spec.loader.exec_module(module)
else:  # pragma: no cover - defensive fallback
    raise RuntimeError("Unable to load local telegram shim")
